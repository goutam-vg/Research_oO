"""LangChain tools (Wikipedia, DuckDuckGo). Results carry numbered sources like [1]."""

import threading
import time

from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, WikipediaAPIWrapper
from langchain_core.tools import Tool

_lock = threading.Lock()  # the two tools may run in parallel threads


def add_source(sources: list, title: str, url: str) -> int:
    """Record a source once (deduplicated by URL) and return its 1-based number (0 if no URL)."""
    if not url:
        return 0
    with _lock:
        for number, source in enumerate(sources, 1):
            if source["url"] == url:
                return number
        sources.append({"title": title or url, "url": url})
        return len(sources)


def _format_item(number: int, title: str, url: str, body: str) -> str:
    head = f"[{number}] {title}" if number else title
    return f"{head}\n{url}\n{body}" if url else f"{head}\n{body}"


def _retry(func, attempts: int = 2, delay: float = 1.0):
    for attempt in range(attempts):
        try:
            return func()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)


def build_tools(sources: list) -> list:
    """Create the tools for ONE research run.

    Every page a tool returns is added to `sources` and shown to the model with its
    number, so the model can cite it inline and the references list is always real.
    """
    wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1500)
    ddg = DuckDuckGoSearchAPIWrapper(max_results=4)

    def wikipedia_lookup(query: str) -> str:
        try:
            docs = wiki.load(query)
        except Exception as error:
            return f"Wikipedia unavailable: {error}"
        if not docs:
            return "No Wikipedia page found."
        items = []
        for doc in docs:
            title = doc.metadata.get("title", "Wikipedia")
            url = doc.metadata.get("source", "")
            number = add_source(sources, f"{title} - Wikipedia", url)
            items.append(_format_item(number, title, url, doc.page_content))
        return "\n\n".join(items)

    def web_search(query: str) -> str:
        try:
            results = _retry(lambda: ddg.results(query, max_results=4))
        except Exception as error:
            return f"Web search unavailable: {error}"
        if not results:
            return "No web results found."
        items = []
        for result in results:
            title = result.get("title", "")
            url = result.get("link", "")
            number = add_source(sources, title, url)
            items.append(_format_item(number, title, url, result.get("snippet", "")))
        return "\n\n".join(items)

    return [
        Tool(
            name="wikipedia_lookup",
            func=wikipedia_lookup,
            description="Look up background information on a topic from Wikipedia.",
        ),
        Tool(
            name="web_search",
            func=web_search,
            description=(
                "Search the web using DuckDuckGo. "
                "Use this for recent news or details Wikipedia does not cover."
            ),
        ),
    ]
