from research_agent.citations import strip_invalid_citations


def test_keeps_valid_and_drops_invalid():
    text = "Cats purr [1]. Dogs bark [7]. Both are pets [2]."
    assert strip_invalid_citations(text, 2) == "Cats purr [1]. Dogs bark. Both are pets [2]."


def test_grouped_citations_are_filtered():
    assert strip_invalid_citations("Fact [1, 9].", 3) == "Fact [1]."
    assert strip_invalid_citations("Fact [8, 9].", 3) == "Fact."


def test_no_sources_removes_all_citations():
    assert strip_invalid_citations("A [1] and B [2].", 0) == "A and B."


def test_years_and_other_brackets_are_untouched():
    assert strip_invalid_citations("Released [2024] [note]", 2) == "Released [2024] [note]"
