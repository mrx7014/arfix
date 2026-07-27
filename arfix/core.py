"""
arfix.core - Arabic text detection, shaping, and BiDi reordering.

This module is the actual "fix" logic and has no knowledge of the CLI,
argument parsing, or installation concerns — it can be imported and used
standalone:

    from arfix.core import fix
    print(fix("some text"))
"""

import re
import arabic_reshaper

# Matches Arabic + Arabic Supplement + Arabic Extended-A + Presentation Forms
ARABIC_RANGE = re.compile(
    r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
)

# Arabic punctuation/spacing that should be treated as part of an Arabic run
ARABIC_NEUTRAL = " \t،؛؟ـ.,"


def has_arabic(text: str) -> bool:
    """Quick check whether a string contains any Arabic-range characters."""
    return bool(ARABIC_RANGE.search(text))


def _is_arabic_char(ch: str) -> bool:
    return bool(ARABIC_RANGE.match(ch))


def _simple_bidi(reshaped_text: str) -> str:
    """
    Pure-Python replacement for python-bidi (no Rust/maturin build step,
    so it installs cleanly on Termux/Android where Rust targets aren't
    supported).

    Splits the line into runs of Arabic-or-neutral vs. other (Latin,
    digits, symbols), reverses the run order for right-to-left visual
    display, and reverses character order within each Arabic run (since
    reshaped glyphs are still stored in logical/typing order). This
    covers the common terminal-output case (a line of Arabic, or Arabic
    mixed with some Latin/numbers) without implementing the full
    Unicode BiDi algorithm.
    """
    tokens = []
    current = ""
    current_is_arabic = None

    for ch in reshaped_text:
        is_arabic = _is_arabic_char(ch) or ch in ARABIC_NEUTRAL
        if current_is_arabic is None:
            current_is_arabic = is_arabic
        if is_arabic == current_is_arabic or ch == " ":
            current += ch
        else:
            tokens.append((current_is_arabic, current))
            current = ch
            current_is_arabic = is_arabic
    if current:
        tokens.append((current_is_arabic, current))

    visual_tokens = []
    for is_arabic, chunk in reversed(tokens):
        visual_tokens.append(chunk[::-1] if is_arabic else chunk)
    return "".join(visual_tokens)


def fix_line(line: str) -> str:
    """Reshape + bidi a single line. Leaves non-Arabic lines untouched."""
    if not has_arabic(line):
        return line
    reshaped = arabic_reshaper.reshape(line)
    return _simple_bidi(reshaped)


def fix(text: str) -> str:
    """Fix a (possibly multi-line) block of text, line by line.

    Processing line-by-line keeps existing line breaks and avoids the
    bidi algorithm reordering separate lines relative to each other.
    """
    lines = text.split("\n")
    return "\n".join(fix_line(line) for line in lines)
