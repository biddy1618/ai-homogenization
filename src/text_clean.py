"""Clean Stack Exchange post bodies (HTML + LaTeX) into plain prose text.

Answer bodies in Posts.xml are stored as HTML. For a language-diversity study we
want the natural-language prose only, so we strip:
  - fenced/inline code (``<pre>``, ``<code>``) — not natural language
  - LaTeX math (``$...$``, ``$$...$$``, ``\\(...\\)``, ``\\[...\\]``)
  - all remaining HTML tags
and normalise whitespace.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

# LaTeX delimiters commonly used on Cross Validated (MathJax).
_MATH_PATTERNS = [
    re.compile(r"\\begin\{.*?\}.*?\\end\{.*?\}", re.DOTALL),  # \begin{align}...\end{align}
    re.compile(r"\$\$.*?\$\$", re.DOTALL),   # $$ ... $$
    re.compile(r"\$.*?\$", re.DOTALL),        # $ ... $
    re.compile(r"\\\(.*?\\\)", re.DOTALL),    # \( ... \)
    re.compile(r"\\\[.*?\\\]", re.DOTALL),    # \[ ... \]
]

# Stray markdown code fences occasionally survive tag removal.
_STRAY_FENCE = re.compile(r"```")

_WHITESPACE = re.compile(r"\s+")


def clean_body(html: str) -> str:
    """Return the natural-language prose from a post's HTML body."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Drop code — it is not natural language and would skew diversity metrics.
    for tag in soup.find_all(["pre", "code"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # Strip LaTeX math after tag removal (bodies keep raw $...$ as text).
    for pattern in _MATH_PATTERNS:
        text = pattern.sub(" ", text)

    text = _STRAY_FENCE.sub(" ", text)

    return _WHITESPACE.sub(" ", text).strip()
