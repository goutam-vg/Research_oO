"""Keeps inline citations like [1] honest: drops numbers that match no real source."""

import re

_CITATION = re.compile(r"(\s?)\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]")


def strip_invalid_citations(text: str, source_count: int) -> str:
    """Remove citation numbers outside 1..source_count (small models sometimes invent them)."""

    def fix(match: re.Match) -> str:
        numbers = [int(n) for n in re.split(r"\s*,\s*", match.group(2))]
        valid = [n for n in numbers if 1 <= n <= source_count]
        if not valid:
            return ""
        return f"{match.group(1)}[{', '.join(str(n) for n in valid)}]"

    return _CITATION.sub(fix, text)
