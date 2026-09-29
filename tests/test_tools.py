from types import SimpleNamespace as NS

from research_agent import tools


class FakeWiki:
    def __init__(self, **kwargs):
        pass

    def load(self, query):
        meta = {"title": "Topic", "source": "https://en.wikipedia.org/wiki/Topic"}
        return [NS(page_content="Wiki body", metadata=meta)]


class FakeDDG:
    def __init__(self, **kwargs):
        pass

    def results(self, query, max_results):
        return [
            {"title": "Web A", "link": "https://a.example", "snippet": "snippet A"},
            {"title": "Dup", "link": "https://en.wikipedia.org/wiki/Topic", "snippet": "dup"},
        ]


class BrokenDDG(FakeDDG):
    def results(self, query, max_results):
        raise RuntimeError("rate limited")


def _tools(monkeypatch, ddg_class):
    monkeypatch.setattr(tools, "WikipediaAPIWrapper", FakeWiki)
    monkeypatch.setattr(tools, "DuckDuckGoSearchAPIWrapper", ddg_class)
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    sources = []
    wiki, web = tools.build_tools(sources)
    return sources, wiki, web


def test_sources_are_numbered_and_deduplicated(monkeypatch):
    sources, wiki, web = _tools(monkeypatch, FakeDDG)
    assert wiki.name == "wikipedia_lookup" and web.name == "web_search"

    wiki_text = wiki.invoke("topic")
    assert "[1] Topic" in wiki_text and "Wiki body" in wiki_text

    web_text = web.invoke("topic")
    assert "[2] Web A" in web_text
    assert "[1] Dup" in web_text  # same URL as the Wikipedia page reuses number 1
    assert [s["url"] for s in sources] == ["https://en.wikipedia.org/wiki/Topic", "https://a.example"]


def test_tool_errors_do_not_crash(monkeypatch):
    sources, _wiki, web = _tools(monkeypatch, BrokenDDG)
    assert "Web search unavailable" in web.invoke("topic")
    assert sources == []
