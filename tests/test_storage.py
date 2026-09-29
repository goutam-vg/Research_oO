import os
from datetime import datetime

from research_agent import storage

SOURCES = [{"title": "Cats - Wikipedia", "url": "https://en.wikipedia.org/wiki/Cat"}]
WHEN = datetime(2026, 1, 2, 3, 4, 5)


def test_txt_format_has_header_summary_and_references():
    text = storage.format_summary("Cats", "- purr [1]", "qwen3:8b", SOURCES, "txt", WHEN)
    assert text.startswith("--- Research Summary ---\nTopic: Cats\n")
    assert "Generated: 2026-01-02 03:04:05" in text
    assert "- purr [1]" in text
    assert "References:\n1. Cats - Wikipedia\n   https://en.wikipedia.org/wiki/Cat" in text


def test_md_format_uses_links():
    text = storage.format_summary("Cats", "- purr [1]", "qwen3:8b", SOURCES, "md", WHEN)
    assert text.startswith("# Cats\n")
    assert "## References" in text
    assert "1. [Cats - Wikipedia](https://en.wikipedia.org/wiki/Cat)" in text


def test_no_sources_message():
    assert "no sources could be retrieved" in storage.format_references([], "txt")


def test_filename_is_safe_and_has_extension():
    name = storage.build_filename("Quantum Computing!?", "md", WHEN)
    assert name == "quantum_computing_20260102_030405.md"
    assert storage.build_filename("???", "txt", WHEN).startswith("summary_")


def test_bad_format_is_rejected():
    try:
        storage.format_summary("x", "y", "m", None, "pdf")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_save_and_list_newest_first(tmp_path):
    first = storage.save_summary("one", "1", str(tmp_path), "txt")
    second = storage.save_summary("two", "2", str(tmp_path), "md")
    os.utime(first, (1_000_000, 1_000_000))
    os.utime(second, (2_000_000, 2_000_000))
    (tmp_path / ".gitkeep").write_text("")
    assert storage.list_summaries(str(tmp_path)) == [second, first]
    assert storage.list_summaries(str(tmp_path / "missing")) == []
