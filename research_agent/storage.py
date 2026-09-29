"""Formatting and saving summaries as .txt or .md files."""

import re
from datetime import datetime
from pathlib import Path

from research_agent.config import FORMAT_CHOICES


def _check_format(fmt: str) -> None:
    if fmt not in FORMAT_CHOICES:
        raise ValueError(f"format must be one of: {', '.join(FORMAT_CHOICES)}")


def build_filename(topic: str, fmt: str = "txt", when: datetime | None = None) -> str:
    _check_format(fmt)
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:50] or "summary"
    return f"{slug}_{(when or datetime.now()):%Y%m%d_%H%M%S}.{fmt}"


def format_references(sources: list[dict], fmt: str = "txt") -> str:
    _check_format(fmt)
    if not sources:
        note = "(none - no sources could be retrieved)"
        return f"## References\n\n{note}" if fmt == "md" else f"References:\n{note}"
    if fmt == "md":
        lines = [
            f"{i}. [{s['title'].replace('[', '(').replace(']', ')')}]({s['url']})"
            for i, s in enumerate(sources, 1)
        ]
        return "## References\n\n" + "\n".join(lines)
    lines = [f"{i}. {s['title']}\n   {s['url']}" for i, s in enumerate(sources, 1)]
    return "References:\n" + "\n".join(lines)


def format_summary(
    topic: str,
    summary: str,
    model: str,
    sources: list[dict] | None = None,
    fmt: str = "txt",
    when: datetime | None = None,
) -> str:
    _check_format(fmt)
    when = when or datetime.now()
    refs = format_references(sources or [], fmt)
    if fmt == "md":
        return f"# {topic}\n\n*Generated {when:%Y-%m-%d %H:%M:%S} · Model: {model}*\n\n{summary}\n\n{refs}\n"
    return (
        "--- Research Summary ---\n"
        f"Topic: {topic}\n"
        f"Generated: {when:%Y-%m-%d %H:%M:%S}\n"
        f"Model: {model}\n"
        "------------------------\n\n"
        f"{summary}\n\n"
        f"{refs}\n"
    )


def save_summary(topic: str, text: str, output_dir: str = "outputs", fmt: str = "txt") -> Path:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / build_filename(topic, fmt)
    path.write_text(text, encoding="utf-8")
    return path


def list_summaries(output_dir: str = "outputs", limit: int = 20) -> list[Path]:
    """Saved summaries, newest first."""
    folder = Path(output_dir)
    if not folder.is_dir():
        return []
    files = [p for p in folder.iterdir() if p.suffix in (".txt", ".md")]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
