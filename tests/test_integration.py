"""Basic integration tests for the full pipeline.

Verifies that the classify → dispatch → respond flow works
end-to-end (TC-I-001).
"""

from decodebot.core.rule_engine import classify_intent
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.session import SessionState


class TestIntegration:
    """Integration tests for the full conversation pipeline."""

    def test_tc_i_001_full_turn_greeting(self):
        """Full turn: greeting → response → history update."""
        session = SessionState()
        intent = classify_intent("hello", session)
        assert intent == Intent.GREETING

        response = dispatch(intent, session)
        assert isinstance(response, str)
        assert len(response) > 0

        session.record_turn("hello", intent, response)
        assert len(session.history) == 1
        recorded_input, recorded_intent, recorded_response = session.history[0]
        assert recorded_input == "hello"
        assert recorded_intent == Intent.GREETING

    def test_full_turn_exit(self):
        """Exit command classifies and dispatches correctly."""
        session = SessionState()
        intent = classify_intent("bye", session)
        assert intent == Intent.EXIT

        response = dispatch(intent, session)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_full_turn_unknown(self):
        """Unknown input classifies and dispatches correctly."""
        session = SessionState()
        intent = classify_intent("foobarbazxyz", session)
        assert intent == Intent.UNKNOWN

        response = dispatch(intent, session)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_full_turn_empty_input(self):
        """Empty input classifies and dispatches correctly."""
        session = SessionState()
        intent = classify_intent("", session)
        assert intent == Intent.EMPTY_INPUT

        response = dispatch(intent, session)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_full_turn_numeric(self):
        """Numeric input classifies and dispatches correctly."""
        session = SessionState()
        intent = classify_intent("42", session)
        assert intent == Intent.NUMERIC_INPUT

        response = dispatch(intent, session)
        assert isinstance(response, str)

    def test_full_turn_symbols(self):
        """Symbols-only input classifies and dispatches correctly."""
        session = SessionState()
        intent = classify_intent("!@#$", session)
        assert intent == Intent.SYMBOLS_ONLY

        response = dispatch(intent, session)
        assert isinstance(response, str)

    def test_deterministic_classification(self):
        """FR-008: Same input always classifies same intent."""
        session = SessionState()
        for _ in range(100):
            assert classify_intent("hello", session) == Intent.GREETING

    def test_history_bound(self):
        """Session history is bounded to 100 entries (FR-067)."""
        session = SessionState()
        for i in range(105):
            classify_intent("hello", session)
            dispatch(Intent.GREETING, session)
            session.record_turn(f"hello_{i}", Intent.GREETING, "Hi!")

        assert len(session.history) == 100
