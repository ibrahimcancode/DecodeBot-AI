"""Tests for unknown/fallback handling (FR-046–FR-053).

Covers TC-UNK-001 through TC-UNK-008.
"""

import pytest

from decodebot.rules import unknown
from decodebot.core.rule_engine import classify_intent
from decodebot.core.intents import Intent
from decodebot.core.session import SessionState


class TestUnknownFallback:
    """Tests for unknown input handling."""

    def test_tc_unk_001_fallback_gibberish(self):
        """Gibberish input produces UNKNOWN intent."""
        session = SessionState()
        intent = classify_intent("asdkjfhalksjdhf", session)
        assert intent == Intent.UNKNOWN

    def test_tc_unk_002_varied_gibberish(self):
        """Various gibberish inputs produce UNKNOWN intent."""
        session = SessionState()
        for gibberish in ["xyzzy", "qwerty", "foobarbaz", "abc123xyz"]:
            intent = classify_intent(gibberish, session)
            assert intent == Intent.UNKNOWN

    def test_unknown_never_crashes(self):
        """UNKNOWN inputs never crash."""
        session = SessionState()
        for text in ["!@#$%", "42", "", "   ", "a" * 1000]:
            try:
                classify_intent(text, session)
            except Exception:
                pytest.fail(f"Crash on input: '{text[:50]}'")

    def test_fallback_response_nonempty(self):
        """Fallback response pool is non-empty."""
        assert len(unknown.FALLBACK_RESPONSES) >= 8

    def test_empty_input_response(self):
        """Empty input returns a gentle prompt."""
        resp = unknown.get_empty_input_response()
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_numeric_response(self):
        """Numeric input returns a number-specific response."""
        resp = unknown.get_numeric_response()
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_symbols_only_response(self):
        """Symbols-only input returns a symbol-specific response."""
        resp = unknown.get_symbols_only_response()
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_escalation_response(self):
        """Escalation response prompts the user to type 'help'."""
        resp = unknown.get_escalation_response()
        assert "help" in resp.lower()

    def test_topic_fallback_weather(self):
        """Weather-related input returns a topic-specific fallback."""
        resp = unknown.topic_fallback("what's the weather like")
        assert resp is not None
        assert isinstance(resp, str)

    def test_topic_fallback_no_match(self):
        """Unrecognized input returns None from topic_fallback."""
        resp = unknown.topic_fallback("completely random input here")
        assert resp is None
