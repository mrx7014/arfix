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
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)

# Presentation forms only. Their presence means the text has already been
# shaped by a previous arfix pass, so it must not be processed again
# (keeps fix() idempotent and prevents double-apply corruption).
PRESENTATION_FORMS = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")

_RTL = "R"
_LTR = "L"
_NEUTRAL = "N"


def has_arabic(text: str) -> bool:
    """Quick check whether a string contains any Arabic-range characters."""
    return bool(ARABIC_RANGE.search(text))


def _char_dir(ch: str) -> str:
    """Classify a single (already reshaped) character by display direction.

    Digits resolve to left-to-right so a number is never reversed. Arabic
    characters resolve to right-to-left. Anything that is neither a letter
    nor a digit (whitespace, punctuation, symbols) is neutral and is
    resolved against its neighbours by ``_resolve_neutrals``.
    """
    if ch.isdigit():
        return _LTR
    if ARABIC_RANGE.match(ch):
        return _RTL
    if ch.isalpha():
        return _LTR
    return _NEUTRAL


def _base_direction(dirs) -> str:
    """Paragraph base direction: the first strong (non-neutral) character.

    Defaults to LTR when the line has no strong character at all.
    """
    for d in dirs:
        if d != _NEUTRAL:
            return d
    return _LTR


def _resolve_neutrals(dirs, base: str):
    """Resolve neutral positions to a surrounding direction (UBA N1/N2).

    A run of neutrals between two strong characters of the same direction
    takes that direction; otherwise it takes the paragraph base direction
    (this also covers neutrals at the start or end of the line).
    """
    resolved = list(dirs)
    n = len(resolved)
    i = 0
    while i < n:
        if resolved[i] != _NEUTRAL:
            i += 1
            continue
        j = i
        while j < n and resolved[j] == _NEUTRAL:
            j += 1
        prev = resolved[i - 1] if i > 0 else None
        nxt = resolved[j] if j < n else None
        d = prev if (prev is not None and prev == nxt) else base
        for k in range(i, j):
            resolved[k] = d
        i = j
    return resolved


def _reorder(text: str, dirs, base: str) -> str:
    """Produce left-to-right visual order for a bidirectionally-naive surface.

    Groups the text into runs of equal direction, reverses the run order for
    an RTL paragraph (so the first logical run lands rightmost), and reverses
    the characters inside each RTL run. LTR runs are left untouched, so Latin
    words, URLs and digit sequences keep their internal left-to-right order.

    This is a single-level approximation of the Unicode BiDi algorithm: it
    covers the common terminal-output case but does not implement nested
    directional embeddings or bracket mirroring.
    """
    runs = []
    cur_dir = dirs[0]
    cur = text[0]
    for ch, d in zip(text[1:], dirs[1:]):
        if d == cur_dir:
            cur += ch
        else:
            runs.append((cur_dir, cur))
            cur_dir, cur = d, ch
    runs.append((cur_dir, cur))

    if base == _RTL:
        runs.reverse()

    return "".join(chunk[::-1] if d == _RTL else chunk for d, chunk in runs)


def fix_line(line: str) -> str:
    """Reshape + bidi a single line. Leaves non-Arabic lines untouched."""
    if not has_arabic(line):
        return line
    if PRESENTATION_FORMS.search(line):
        # Already shaped by a previous pass: never re-process (idempotent).
        return line

    reshaped = arabic_reshaper.reshape(line)
    dirs = [_char_dir(ch) for ch in reshaped]
    if not dirs:
        return reshaped
    base = _base_direction(dirs)
    resolved = _resolve_neutrals(dirs, base)
    return _reorder(reshaped, resolved, base)


def fix(text: str) -> str:
    """Fix a (possibly multi-line) block of text, line by line.

    Processing line-by-line keeps existing line breaks and avoids the
    bidi algorithm reordering separate lines relative to each other.
    """
    lines = text.split("\n")
    return "\n".join(fix_line(line) for line in lines)
