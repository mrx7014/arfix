"""
Tests for arfix.core - shaping, BiDi reordering, and detection.

These lock in the behaviour fixed after the review:
  - mixed Arabic/Latin lines must not mangle Latin words, URLs, or digits
  - an English sentence containing one Arabic word must keep its English
    word order (no base-direction guessing that swaps LTR fragments)
  - fix() must be idempotent (applying it twice equals applying it once)
"""

import arabic_reshaper

from arfix.core import fix, fix_line, has_arabic

PRESENTATION_FORMS = range(0xFB50, 0xFE00)  # rough split, see core for exactness


def _has_presentation_forms(text: str) -> bool:
    return any(
        0xFB50 <= ord(ch) <= 0xFDFF or 0xFE70 <= ord(ch) <= 0xFEFF for ch in text
    )


# --- detection -------------------------------------------------------------


def test_has_arabic_true():
    assert has_arabic("مرحبا")


def test_has_arabic_false():
    assert not has_arabic("hello world 123")


# --- passthrough -----------------------------------------------------------


def test_non_arabic_line_untouched():
    assert (
        fix_line("just plain english, 42% of it.") == "just plain english, 42% of it."
    )


# --- pure Arabic -----------------------------------------------------------


def test_pure_arabic_is_shaped_and_reversed():
    out = fix("مرحبا")
    # shaped into presentation forms
    assert _has_presentation_forms(out)
    # not the same logical string
    assert out != "مرحبا"


# --- finding 1: URLs / Latin runs must survive -----------------------------


def test_mixed_line_keeps_url_intact():
    src = 'وش المقصود بس "عليه متاح في ksaonline.com"؟'
    out = fix(src)
    assert "ksaonline.com" in out, out


def test_digits_not_reversed():
    out = fix("مرحبا 1234")
    assert "1234" in out, out


# --- finding 3: English sentence keeps its word order ----------------------


def test_english_fragments_keep_order():
    src = "Notes, and lists: مرحبا بالعالم. Done."
    out = fix(src)
    assert out.startswith("Notes, and lists:"), out
    assert out.endswith(". Done."), out


def test_latin_run_not_reversed_in_rtl_line():
    src = "مرحبا hello world"
    out = fix(src)
    assert "hello world" in out, out


# --- finding 2: idempotency (double-apply must be a no-op) -----------------


def test_fix_is_idempotent():
    src = "وش المقصود بس ksaonline.com؟"
    once = fix(src)
    assert fix(once) == once


def test_fix_idempotent_mixed():
    src = "Notes: مرحبا. Done."
    once = fix(src)
    assert fix(once) == once


# --- multi-line ------------------------------------------------------------


def test_multiline_line_independent():
    src = "مرحبا\n\nhello"
    out = fix(src)
    lines = out.split("\n")
    assert lines[1] == ""
    assert lines[2] == "hello"
