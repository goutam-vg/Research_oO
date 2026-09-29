from types import SimpleNamespace as NS

from research_agent import agent

TOOL_CALLS = NS(
    type="AIMessageChunk",
    content="",
    tool_call_chunks=[{"name": "wikipedia_lookup"}, {"name": "web_search"}],
)
TOOL_RESULT = NS(type="tool", content="result")


def _token(text):
    return NS(type="AIMessageChunk", content=text, tool_call_chunks=[])


class FakeAgent:
    def __init__(self, chunks):
        self.chunks = chunks

    def stream(self, *args, **kwargs):
        for chunk in self.chunks:
            yield chunk, {}


class FakeLLM:
    def stream(self, messages):
        for text in ["Fallback ", "answer [1] [9]"]:
            yield NS(content=text)


def _setup(monkeypatch, chunks):
    def fake_build_tools(sources):
        sources.append({"title": "Src", "url": "https://src.example"})
        return [
            NS(name="wikipedia_lookup", invoke=lambda q: "[1] Src\nwiki text"),
            NS(name="web_search", invoke=lambda q: "[1] Src\nweb text"),
        ]

    monkeypatch.setattr(agent, "build_tools", fake_build_tools)
    monkeypatch.setattr(agent, "_make_llm", lambda *a, **k: FakeLLM())
    monkeypatch.setattr(agent, "create_agent", lambda **k: FakeAgent(chunks))


def test_agent_path_streams_tokens_and_cleans_citations(monkeypatch):
    chunks = [TOOL_CALLS, TOOL_RESULT, TOOL_RESULT, _token("Hello [1] "), _token("world [5]")]
    _setup(monkeypatch, chunks)
    events = list(agent.research_stream("topic"))

    statuses = [e["text"] for e in events if e["type"] == "status"]
    assert "Searching Wikipedia" in statuses and "Searching the web" in statuses
    assert "".join(e["text"] for e in events if e["type"] == "token") == "Hello [1] world [5]"
    assert events[-1] == {
        "type": "done",
        "summary": "Hello [1] world",  # invented [5] is removed
        "sources": [{"title": "Src", "url": "https://src.example"}],
    }


def test_safety_net_when_model_skips_tools(monkeypatch):
    _setup(monkeypatch, [_token("Ungrounded answer from memory")])
    events = list(agent.research_stream("topic"))

    tokens = "".join(e["text"] for e in events if e["type"] == "token")
    assert "Ungrounded" not in tokens  # never shown to the user
    assert tokens == "Fallback answer [1] [9]"
    assert events[-1]["summary"] == "Fallback answer [1]"
    assert any(e.get("text") == "Searching Wikipedia and the web" for e in events)


def test_research_returns_summary_and_sources(monkeypatch):
    _setup(monkeypatch, [TOOL_CALLS, TOOL_RESULT, _token("Done [1]")])
    summary, sources = agent.research("topic", length="short")
    assert summary == "Done [1]" and len(sources) == 1


def test_bad_length_is_rejected(monkeypatch):
    _setup(monkeypatch, [])
    try:
        list(agent.research_stream("topic", length="huge"))
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_prompts_reflect_length_and_language():
    prompt = agent.build_system_prompt("short", "Spanish")
    assert "3 key points" in prompt and "Spanish" in prompt
    assert "12 key points" in agent.build_fallback_prompt("long", "English")
