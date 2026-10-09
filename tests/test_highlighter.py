import pytest
from rich.text import Text
from calc.highlighter import BracketHighlighter, RAINBOW_COLORS, UNMATCHED_STYLE, SyntaxHighlighter, SI_NUM_STYLE


def test_bracket_highlighter_no_brackets():
    hl = BracketHighlighter()
    t = Text("123 + 456 * 789")
    hl.highlight(t)
    # No spans added
    assert len(t.spans) == 0


def test_bracket_highlighter_single_pair():
    hl = BracketHighlighter()
    t = Text("(1 + 2)")
    hl.highlight(t)
    # 2 spans: '(' at 0 and ')' at 6, both level 0
    assert len(t.spans) == 2
    span_open = next(s for s in t.spans if s.start == 0 and s.end == 1)
    span_close = next(s for s in t.spans if s.start == 6 and s.end == 7)
    assert span_open.style == RAINBOW_COLORS[0]
    assert span_close.style == RAINBOW_COLORS[0]


def test_bracket_highlighter_nested_pairs():
    hl = BracketHighlighter()
    # (1 + (2 * (3 + 4)))
    # 0    5    10 15 1718
    t = Text("(1 + (2 * (3 + 4)))")
    hl.highlight(t)
    assert len(t.spans) == 6

    # Outer pair: index 0 and 18 -> level 0
    s0 = next(s for s in t.spans if s.start == 0)
    s18 = next(s for s in t.spans if s.start == 18)
    assert s0.style == RAINBOW_COLORS[0]
    assert s18.style == RAINBOW_COLORS[0]

    # Mid pair: index 5 and 17 -> level 1
    s5 = next(s for s in t.spans if s.start == 5)
    s17 = next(s for s in t.spans if s.start == 17)
    assert s5.style == RAINBOW_COLORS[1]
    assert s17.style == RAINBOW_COLORS[1]

    # Inner pair: index 10 and 16 -> level 2
    s10 = next(s for s in t.spans if s.start == 10)
    s16 = next(s for s in t.spans if s.start == 16)
    assert s10.style == RAINBOW_COLORS[2]
    assert s16.style == RAINBOW_COLORS[2]


def test_bracket_highlighter_unmatched_brackets():
    hl = BracketHighlighter()
    # Extra open: (1 + 2
    t1 = Text("(1 + 2")
    hl.highlight(t1)
    assert len(t1.spans) == 1
    assert t1.spans[0].style == UNMATCHED_STYLE

    # Extra close: 1 + 2)
    t2 = Text("1 + 2)")
    hl.highlight(t2)
    assert len(t2.spans) == 1
    assert t2.spans[0].style == UNMATCHED_STYLE

    # Mismatched in middle: (1 + 2)) + (3
    t3 = Text("(1 + 2)) + (3")
    hl.highlight(t3)
    # (1 + 2) -> matched (level 0)
    # ) at index 7 -> unmatched
    # ( at index 11 -> unmatched
    s_matched = [s for s in t3.spans if s.style == RAINBOW_COLORS[0]]
    s_unmatched = [s for s in t3.spans if s.style == UNMATCHED_STYLE]
    assert len(s_matched) == 2
    assert len(s_unmatched) == 2


# ---------------------------------------------------------------------------
# SyntaxHighlighter tests
# ---------------------------------------------------------------------------

def test_syntax_highlighter_si_num_no_brackets():
    """SI-prefix number in a plain expression gets highlighted."""
    hl = SyntaxHighlighter()
    t = Text("10k * 2")
    hl.highlight(t)
    # "10k" (index 0-3) should have SI_NUM_STYLE
    si_spans = [s for s in t.spans if s.style == SI_NUM_STYLE]
    assert len(si_spans) == 1
    assert si_spans[0].start == 0 and si_spans[0].end == 3


def test_syntax_highlighter_si_num_with_brackets():
    """Both bracket and SI-prefix highlighting applied together."""
    hl = SyntaxHighlighter()
    t = Text("(1.5M + 100n)")
    hl.highlight(t)
    si_spans = [s for s in t.spans if s.style == SI_NUM_STYLE]
    assert len(si_spans) == 2  # "1.5M" and "100n"


def test_syntax_highlighter_no_si_plain_numbers():
    """Plain numbers without SI suffix produce no SI spans."""
    hl = SyntaxHighlighter()
    t = Text("123 + 456")
    hl.highlight(t)
    si_spans = [s for s in t.spans if s.style == SI_NUM_STYLE]
    assert len(si_spans) == 0


def test_syntax_highlighter_multiple_si():
    """Multiple SI-prefix numbers in one expression all get highlighted."""
    hl = SyntaxHighlighter()
    t = Text("10k + 1M - 5u")
    hl.highlight(t)
    si_spans = [s for s in t.spans if s.style == SI_NUM_STYLE]
    assert len(si_spans) == 3
