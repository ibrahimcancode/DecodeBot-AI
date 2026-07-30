"""Tests for greeting detection (FR-026–FR-035).

Covers TC-GREET-001 through TC-GREET-010.
"""

import pytest

from decodebot.rules import greetings
from decodebot.utils.normalization import normalize


class TestGreetingDetection:
    """Tests for greeting pattern matching."""

    @pytest.mark.parametrize("phrase", [
        "hi",
        "hello",
        "hey",
        "yo",
        "good morning",
        "good afternoon",
        "good evening",
        "greetings",
        "howdy",
        "sup",
        "what's up",
    ])
    def test_tc_greet_basic_greetings(self, phrase):
        """TC-GREET-001..011: Basic greeting phrases are recognized."""
        assert greetings.matches(normalize(phrase)), f"'{phrase}' should be a greeting"

    def test_tc_greet_case_insensitive(self):
        """Case variations are recognized."""
        assert greetings.matches(normalize("HELLO!"))
        assert greetings.matches(normalize("Hello"))

    def test_tc_greet_with_context(self):
        """Greeting within a longer sentence is recognized."""
        assert greetings.matches(normalize("hey there"))
        assert greetings.matches(normalize("hi, how are you"))

    def test_tc_greet_word_boundary_safety(self):
        """TC-U-005: 'history' does NOT match as greeting."""
        assert not greetings.matches(normalize("history"))

    def test_tc_greet_mixed_sentence(self):
        """TC-U-006: 'hi, tell me the history' IS a greeting (contains 'hi')."""
        assert greetings.matches(normalize("hi, tell me the history"))

    def test_greeting_response_pool_nonempty(self):
        """GREETING_RESPONSES is non-empty."""
        assert len(greetings.GREETING_RESPONSES) >= 8

    def test_greeting_response_variety(self):
        """At least 4 distinct responses across many calls."""
        from decodebot.rules.greetings import get_response
        import random
        random.seed(42)
        responses = {get_response() for _ in range(100)}
        assert len(responses) >= 4

    def test_welcome_response_on_first_greeting(self):
        """First greeting returns the welcome variant."""
        from decodebot.rules.greetings import get_response, WELCOME_RESPONSE
        result = get_response(is_first_greeting=True)
        assert result == WELCOME_RESPONSE

    def test_greeting_patterns_abundant(self):
        """At least 15 distinct greeting patterns exist (FR-026)."""
        assert len(greetings.GREETING_PATTERNS) >= 15
