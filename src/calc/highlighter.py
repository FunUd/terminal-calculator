"""Rainbow bracket and syntax highlighter for expressions."""

import re

from rich.highlighter import Highlighter
from rich.text import Text

# Rainbow bracket colors by nesting depth
RAINBOW_COLORS = [
    "bold #FFD700",  # Gold / Yellow
    "bold #00E5FF",  # Bright Cyan
    "bold #FF4081",  # Pink / Magenta
    "bold #76FF03",  # Bright Green
    "bold #E040FB",  # Purple
    "bold #FF9100",  # Bright Orange
]

# Highlight style for unmatched brackets
UNMATCHED_STYLE = "bold white on red"

# Highlight style for SI-prefix numbers (e.g. 10k, 1.5M, 100n)
SI_NUM_STYLE = "bold #76FF03"  # Bright Green

# Regex matching SI-prefix numbers (same pattern as TOKEN_SPEC SI_NUM in parser.py)
_SI_NUM_RE = re.compile(r"(?:\d+\.\d*|\.\d+|\d[\d_]*)(?:[kKMGmunp])")


class BracketHighlighter(Highlighter):
    """Highlighter that colors matching parentheses with rainbow colors and flags unmatched ones."""

    def highlight(self, text: Text) -> None:
        plain = text.plain
        stack: list[tuple[int, int]] = []  # (index, level)
        matched: list[tuple[int, int]] = []  # (index, level)
        unmatched: list[int] = []  # index

        for i, ch in enumerate(plain):
            if ch == "(":
                level = len(stack)
                stack.append((i, level))
            elif ch == ")":
                if stack:
                    opening_idx, level = stack.pop()
                    matched.append((opening_idx, level))
                    matched.append((i, level))
                else:
                    unmatched.append(i)

        # Any unclosed opening brackets in stack are unmatched
        for idx, _ in stack:
            unmatched.append(idx)

        # Apply styles to text spans
        color_count = len(RAINBOW_COLORS)
        for idx, level in matched:
            color = RAINBOW_COLORS[level % color_count]
            text.stylize(color, idx, idx + 1)

        for idx in unmatched:
            text.stylize(UNMATCHED_STYLE, idx, idx + 1)


class SyntaxHighlighter(BracketHighlighter):
    """Extends BracketHighlighter with SI-prefix number highlighting.

    SI-prefix numbers (e.g. 10k, 1.5M, 100n) are highlighted with SI_NUM_STYLE
    in addition to the rainbow bracket coloring inherited from BracketHighlighter.
    """

    def highlight(self, text: Text) -> None:
        # Apply bracket highlighting first
        super().highlight(text)
        # Then overlay SI-prefix number highlighting
        plain = text.plain
        for m in _SI_NUM_RE.finditer(plain):
            text.stylize(SI_NUM_STYLE, m.start(), m.end())
