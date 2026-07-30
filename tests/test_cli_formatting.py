import pytest

from decodebot.utils.terminal import clear_screen, get_terminal_width, supports_color
from decodebot.utils.levenshtein import levenshtein, fuzzy_suggest
from decodebot.utils.formatting import box_text, get_terminal_width as fmt_width


class TestLevenshtein:
    def test_exact_match(self):
        assert levenshtein("help", "help") == 0

    def test_distance_one(self):
        assert levenshtein("help", "hel") == 1
        assert levenshtein("help", "halp") == 1

    def test_distance_two(self):
        assert levenshtein("help", "halp") <= 2

    def test_fuzzy_suggest_help(self):
        result = fuzzy_suggest("halp")
        assert result == "help"

    def test_fuzzy_suggest_exit(self):
        result = fuzzy_suggest("exti")
        assert result == "exit"

    def test_no_suggestion_for_distant(self):
        result = fuzzy_suggest("asdfghjkl")
        assert result is None


class TestTerminal:
    def test_terminal_width_positive(self):
        width = get_terminal_width()
        assert width > 0

    def test_clear_screen_does_not_crash(self):
        try:
            clear_screen()
        except Exception:
            pytest.fail("clear_screen raised exception")


class TestFormatting:
    def test_box_text_contains_lines(self):
        result = box_text(["hello", "world"])
        assert "hello" in result
        assert "world" in result

    def test_box_text_title(self):
        result = box_text(["content"], title="Test")
        assert "Test" in result
