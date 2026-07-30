"""Unit tests for input normalization (FR-013–FR-024).

Covers TC-U-001, TC-U-002, TC-U-003, and related edge cases.
"""

import pytest

from decodebot.utils.normalization import (
    normalize,
    is_numeric_only,
    is_symbols_only,
    is_whitespace_only,
)


class TestNormalize:
    """Tests for the normalize() function."""

    def test_tc_u_001_strip_and_lowercase(self):
        """TC-U-001: normalize('  Hello  ') returns 'hello'."""
        assert normalize("  Hello  ") == "hello"

    def test_tc_u_002_punctuation_stripped(self):
        """TC-U-002: normalize('HELLO!!!') returns 'hello'."""
        assert normalize("HELLO!!!") == "hello"

    def test_tc_u_003_whitespace_collapsed(self):
        """TC-U-003: normalize('hi\\t\\nthere') returns 'hi there'."""
        assert normalize("hi\t\nthere") == "hi there"

    def test_empty_string(self):
        """Empty input normalizes to empty string."""
        assert normalize("") == ""

    def test_whitespace_only(self):
        """Whitespace-only input normalizes to empty string."""
        assert normalize("   ") == ""

    def test_mixed_case(self):
        """Mixed case input is lowercased."""
        assert normalize("HeLLo WoRLd") == "hello world"

    def test_trailing_punctuation(self):
        """Trailing punctuation is stripped."""
        assert normalize("hello!!!") == "hello"
        assert normalize("hello?") == "hello"
        assert normalize("hello.") == "hello"

    def test_internal_whitespace_collapsed(self):
        """Internal runs of spaces are collapsed."""
        assert normalize("hello    there") == "hello there"

    def test_unicode_safe(self):
        """Non-ASCII Unicode does not crash."""
        result = normalize("héllo")
        assert isinstance(result, str)

    def test_control_characters_stripped(self):
        """Control characters are removed."""
        result = normalize("hello\r\n")
        assert "hello\r".strip() == "" or result == "hello"

    def test_tc_u_010_is_numeric_only_true(self):
        """TC-U-010: is_numeric_only('42') returns True."""
        assert is_numeric_only("42") is True

    def test_tc_u_011_is_numeric_only_false(self):
        """TC-U-011: is_numeric_only('42abc') returns False."""
        assert is_numeric_only("42abc") is False

    def test_is_numeric_negative(self):
        """Negative numbers are numeric."""
        assert is_numeric_only("-42") is True

    def test_is_numeric_decimal(self):
        """Decimals are numeric."""
        assert is_numeric_only("3.14") is True

    def test_is_numeric_comma(self):
        """Comma-separated thousands are numeric."""
        assert is_numeric_only("1,000") is True

    def test_tc_u_012_is_symbols_only_true(self):
        """TC-U-012: is_symbols_only('!@#$') returns True."""
        assert is_symbols_only("!@#$") is True

    def test_tc_u_013_is_symbols_only_false(self):
        """TC-U-013: is_symbols_only('a!@#') returns False."""
        assert is_symbols_only("a!@#") is False

    def test_is_symbols_only_empty(self):
        """Empty string is not symbols-only."""
        assert is_symbols_only("") is False

    def test_is_whitespace_only_true(self):
        """is_whitespace_only with spaces returns True."""
        assert is_whitespace_only("   ") is True

    def test_is_whitespace_only_false(self):
        """is_whitespace_only with text returns False."""
        assert is_whitespace_only("hello") is False
