"""The research agent: streams progress + answer, with a safety net if tools are skipped."""

import os
import re
from concurrent.futures import ThreadPoolExecutor

from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from research_agent.citations import strip_invalid_citations
from research_agent.config import get_base_url, get_model_name
from research_agent.tools import build_tools

STRUCTURES = {
    "short": "a 1-2 sentence overview followed by 3 key points as '- ' bullets",
    "medium": "a 2-3 sentence overview, 5-8 key points as '- ' bullets, and a one-line conclusion",
    "long": "an overview paragraph, 8-12 key points as '- ' bullets, and a 2-3 sentence conclusion",
}
LENGTH_TOKENS = {"short": 500, "medium": 1000, "long": 1800}

TOOL_LABELS = {
    "wikipedia_lookup": "Searching Wikipedia",
    "web_search": "Searching the web",
}


def _format_rules(length: str, lang: str) -> str:
    return (
        f"Reply in plain text with: {STRUCTURES[length]}. "
        "Cite sources inline using the bracketed numbers from the source material, "
        "like [1] or [2], right after the claim they support; never invent a number. "
        f"Write the summary in {lang}. "
        "Do NOT write a references or sources section; it is added automatically. "
        "Do not invent facts; if the sources contain nothing useful, say so."
    )


def build_system_prompt(length: str = "medium", lang: str = "English") -> str:
    return (
        "You are a research assistant that writes clear, factual topic summaries. "
        "Do not write any text before calling tools. First call wikipedia_lookup and "
        "web_search TOGETHER in the same step (in parallel), using the topic as the query. "
        "Base the summary only on what the tools return. " + _format_rules(length, lang)
    )


def build_fallback_prompt(length: str = "medium", lang: str = "English") -> str:
    return (
        "You are a research assistant that writes clear, factual topic summaries. "
        "Base the summary only on the source material provided by the user. "
        + _format_rules(length, lang)
    )


def _make_llm(model: str | None = None, length: str = "medium", **overrides) -> ChatOllama:
    settings = dict(
        model=get_model_name(model),
        base_url=get_base_url(),
        temperature=0,
        # Keep the model loaded in memory between requests (avoids reload delay).
        keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
        # Thinking models (e.g. qwen3) are much slower with reasoning on.
        reasoning=os.getenv("OLLAMA_REASONING", "false").lower() == "true",
        # Cap the summary length so generation always finishes quickly.
        num_predict=int(os.getenv("OLLAMA_NUM_PREDICT") or LENGTH_TOKENS[length]),
    )
    settings.update(overrides)
    return ChatOllama(**settings)


def warm_up(model: str | None = None) -> None:
    """Load the model into memory ahead of time. Safe to call in a background thread."""
    try:
        _make_llm(model, num_predict=1).invoke("ok")
    except Exception:
        pass  # best effort; the real request will report any problem


def _content_to_text(content) -> str:
    """Message content can be a string or a list of parts; flatten to text."""
    if isinstance(content, str):
        return content
    parts = []
    for part in content or []:
        if isinstance(part, dict):
            parts.append(str(part.get("text") or part.get("content") or ""))
        else:
            parts.append(str(part))
    return " ".join(p for p in parts if p)


def _clean(text: str) -> str:
    """Remove <think>...</think> reasoning blocks that some models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _fallback(llm, tools, topic: str, length: str, lang: str):
    """Safety net: run the searches directly, then have the model summarize them.

    Used when the model tries to answer from memory instead of calling its tools
    (common with small models). Returns the streamed answer text.
    """
    yield {"type": "status", "text": "Searching Wikipedia and the web"}
    with ThreadPoolExecutor(max_workers=len(tools)) as pool:
        results = list(pool.map(lambda tool: tool.invoke(topic), tools))

    yield {"type": "status", "text": "Writing summary"}
    messages = [
        ("system", build_fallback_prompt(length, lang)),
        ("human", f"Topic: {topic}\n\nSource material:\n\n" + "\n\n".join(results)),
    ]
    answer = ""
    for chunk in llm.stream(messages):
        text = _content_to_text(chunk.content)
        if text:
            answer += text
            yield {"type": "token", "text": text}
    return answer


def research_stream(
    topic: str, model: str | None = None, length: str = "medium", lang: str = "English"
):
    """Research `topic`, yielding events as they happen:

    {"type": "status", "text": "Searching Wikipedia"}      progress label
    {"type": "token",  "text": "..."}                      piece of the answer (typing effect)
    {"type": "done",   "summary": str, "sources": [...]}   final result
    """
    if length not in STRUCTURES:
        raise ValueError(f"length must be one of: {', '.join(STRUCTURES)}")

    sources: list[dict] = []
    tools = build_tools(sources)
    llm = _make_llm(model, length)
    agent = create_agent(model=llm, tools=tools, system_prompt=build_system_prompt(length, lang))

    yield {"type": "status", "text": "Thinking"}
    answer = ""
    tools_used = False

    stream = agent.stream(
        {"messages": [{"role": "user", "content": f"Research and summarize this topic: {topic}"}]},
        stream_mode="messages",
    )
    for chunk, _meta in stream:
        kind = getattr(chunk, "type", "")

        if kind == "tool":  # a tool finished; the model is about to write
            tools_used = True
            yield {"type": "status", "text": "Writing summary"}
            continue
        if kind not in ("AIMessageChunk", "ai"):
            continue

        calls = getattr(chunk, "tool_call_chunks", None) or []
        for call in calls:
            if call.get("name"):
                tools_used = True
                yield {"type": "status", "text": TOOL_LABELS.get(call["name"], f"Using {call['name']}")}

        text = _content_to_text(chunk.content)
        if text and not calls:
            if not tools_used:  # answering from memory: discard it and use the safety net
                answer = ""
                break
            answer += text
            yield {"type": "token", "text": text}
    getattr(stream, "close", lambda: None)()

    if not answer.strip():
        answer = yield from _fallback(llm, tools, topic, length, lang)

    summary = strip_invalid_citations(_clean(answer), len(sources))
    if not summary:
        raise RuntimeError("The agent returned no answer.")
    yield {"type": "done", "summary": summary, "sources": sources}


def research(
    topic: str, model: str | None = None, length: str = "medium", lang: str = "English"
) -> tuple[str, list[dict]]:
    """Non-streaming helper: returns (summary_text, sources)."""
    for event in research_stream(topic, model, length, lang):
        if event["type"] == "done":
            return event["summary"], event["sources"]
    raise RuntimeError("The agent returned no answer.")
