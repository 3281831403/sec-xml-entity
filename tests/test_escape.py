"""XML escaping acceptance tests: 10 defect checks plus 5 cross-checks.

The tests are intentionally strict.  Every assertion fixes an exact string or
an exact boolean; no test accepts a prefix, a normalized variant, or a
length-only match.  In the initial repository every test fails at its first
call because the implementation stubs raise NotImplementedError.
"""

import pytest

from xmlesc.escape import (
    escape_attr,
    escape_batch,
    escape_once,
    escape_text,
    normalize_entity,
    roundtrip_ok,
    unescape,
    valid_codepoint,
)


def test_defect_01_escape_text_escapes_ampersand():
    """Defect 1: escaping only angle brackets leaves a raw ampersand."""
    assert escape_text("R&D <admin>") == "R&amp;D &lt;admin&gt;"


def test_defect_02_escape_attr_escapes_double_quote():
    """Defect 2: an unescaped double quote ends a double-quoted attribute."""
    assert (
        escape_attr('role="admin" & <root>', '"')
        == "role=&quot;admin&quot; &amp; &lt;root&gt;"
    )


def test_defect_03_escape_attr_escapes_single_quote():
    """Defect 3: an unescaped single quote truncates a single-quoted value."""
    assert (
        escape_attr("name='O'Brien' & <x>", "'")
        == "name=&apos;O&apos;Brien&apos; &amp; &lt;x&gt;"
    )


def test_defect_04_unescape_supports_hexadecimal_references():
    """Defect 4: hexadecimal references must decode, not pass through."""
    assert (
        unescape("decimal &#65; hex &#x42; upper &#X43;")
        == "decimal A hex B upper C"
    )


def test_defect_05_unescape_rejects_control_references():
    """Defect 5: control code points must not be accepted by unescape."""
    with pytest.raises(ValueError):
        unescape("bad &#8; control")


def test_defect_06_valid_codepoint_rejects_surrogate_range():
    """Defect 6: the surrogate range is not legal XML character data."""
    assert valid_codepoint(0xD800) is False
    assert valid_codepoint(0xDFFF) is False
    assert valid_codepoint(0xE000) is True


def test_defect_07_normalize_entity_uses_decimal_for_every_base():
    """Defect 7: decimal and hexadecimal spellings must collapse together."""
    assert (
        normalize_entity("A &#x41; B &#65; C &#X1F600;")
        == "A &#65; B &#65; C &#128512;"
    )


def test_defect_08_escape_once_does_not_double_escape():
    """Defect 8: existing entities must not be escaped a second time."""
    once = escape_once("&amp; <tag> &")
    assert once == "&amp; &lt;tag&gt; &amp;"
    assert escape_once(once) == once


def test_defect_09_roundtrip_ok_compares_content_not_length():
    """Defect 9: a same-length invalid input is not a successful round trip."""
    assert roundtrip_ok("A&B <tag> \"q\" 'p'") is True
    assert roundtrip_ok("\x01") is False


def test_defect_10_escape_batch_keeps_quote_context_per_entry():
    """Defect 10: the second entry must not inherit the first quote type."""
    texts = {"first": 'say "hello"', "second": "it's fine"}
    policy = {"first": "attr_double", "second": "attr_single"}

    result = escape_batch(texts, policy)

    assert result == {
        "first": "say &quot;hello&quot;",
        "second": "it&apos;s fine",
    }
    assert result["second"] == escape_attr(texts["second"], "'")


def test_escape_text_transforms_all_five_predefined_characters():
    """Cross-check: each of the five predefined characters is transformed."""
    source = "&<>\"'"
    escaped = escape_text(source)

    assert escaped == "&amp;&lt;&gt;&quot;&apos;"
    assert escaped.count("&") == 5
    assert all(character not in escaped for character in "<>\"'")


def test_escape_then_unescape_returns_original():
    """Cross-check: escape followed by one-pass unescape is lossless."""
    original = """A&B <tag attr="v"> 'single'"""
    assert unescape(escape_text(original)) == original


def test_hexadecimal_character_reference_is_decoded():
    """Cross-check: a supplementary-plane hexadecimal reference decodes."""
    assert unescape("smile &#x1F642; end") == "smile \U0001F642 end"


def test_invalid_codepoint_is_rejected():
    """Cross-check: out-of-range code points are not accepted anywhere."""
    assert valid_codepoint(-1) is False
    assert valid_codepoint(0x110000) is False
    with pytest.raises(ValueError):
        unescape("&#x110000;")


def test_batches_match_individual_escaping():
    """Cross-check: two batches are independent and match single calls."""
    first_texts = {"plain": "A&B", "double": 'say "hi"', "single": "it's ok"}
    first_policy = {
        "plain": "text",
        "double": "attr_double",
        "single": "attr_single",
    }
    first_expected = {
        "plain": escape_text(first_texts["plain"]),
        "double": escape_attr(first_texts["double"], '"'),
        "single": escape_attr(first_texts["single"], "'"),
    }
    assert escape_batch(first_texts, first_policy) == first_expected

    second_texts = {"plain": "<x>", "double": 'a"b', "single": "c'd"}
    second_policy = {
        "plain": "text",
        "double": "attr_double",
        "single": "attr_single",
    }
    second_expected = {
        "plain": escape_text(second_texts["plain"]),
        "double": escape_attr(second_texts["double"], '"'),
        "single": escape_attr(second_texts["single"], "'"),
    }
    assert escape_batch(second_texts, second_policy) == second_expected
    assert first_expected != second_expected