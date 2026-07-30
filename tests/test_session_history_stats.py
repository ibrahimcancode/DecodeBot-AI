import pytest
import time

from decodebot.core.session import SessionState
from decodebot.core.intents import Intent
from decodebot.core.history import get_history_text
from decodebot.core.stats import get_session_duration
from decodebot.core.rule_engine import classify_intent


class TestSessionState:
    def test_session_initial_state(self):
        s = SessionState()
        assert s.history == []
        assert s.consecutive_unknown == 0
        assert s.message_count == 0
        assert s.user_name is None
        assert s.intent_counts == {}

    def test_record_turn_updates_counts(self):
        s = SessionState()
        s.record_turn("hello", Intent.GREETING, "Hi!")
        assert s.message_count == 1
        assert s.intent_counts.get("GREETING") == 1

    def test_empty_input_does_not_increment_count(self):
        s = SessionState()
        s.record_turn("", Intent.EMPTY_INPUT, "...")
        assert s.message_count == 0

    def test_consecutive_unknown_tracking(self):
        s = SessionState()
        s.record_turn("x", Intent.UNKNOWN, "...")
        assert s.consecutive_unknown == 1
        s.record_turn("y", Intent.UNKNOWN, "...")
        assert s.consecutive_unknown == 2
        s.record_turn("hello", Intent.GREETING, "Hi!")
        assert s.consecutive_unknown == 0

    def test_history_bound_to_100(self):
        s = SessionState()
        for i in range(105):
            s.record_turn(f"msg_{i}", Intent.UNKNOWN, "ok")
        assert len(s.history) == 100
        assert s.history[0][0] == "msg_5"
        assert s.history[-1][0] == "msg_104"

    def test_reset_clears_state(self):
        s = SessionState()
        s.user_name = "Bob"
        s.record_turn("hello", Intent.GREETING, "Hi!")
        s.reset()
        assert s.history == []
        assert s.message_count == 0
        assert s.user_name is None
        assert s.intent_counts == {}

    def test_intent_counts_tracking(self):
        s = SessionState()
        s.record_turn("hi", Intent.GREETING, "Hi!")
        s.record_turn("hi", Intent.GREETING, "Hi!")
        s.record_turn("bye", Intent.EXIT, "Bye!")
        s.record_turn("foo", Intent.UNKNOWN, "...")
        assert s.intent_counts["GREETING"] == 2
        assert s.intent_counts["EXIT"] == 1
        assert s.intent_counts["UNKNOWN"] == 1

    def test_session_duration_format(self):
        s = SessionState()
        s.start_time = time.monotonic() - 125
        dur = get_session_duration(s)
        assert "m" in dur or "s" in dur

    def test_empty_history_text(self):
        s = SessionState()
        text = get_history_text(s)
        assert text == "No conversation yet!"

    def test_history_text_with_entries(self):
        s = SessionState()
        s.record_turn("hello", Intent.GREETING, "Hi!")
        text = get_history_text(s)
        assert "hello" in text
        assert "Hi!" in text

    def test_deterministic_classification_unchanged(self):
        s = SessionState()
        for _ in range(100):
            assert classify_intent("hello", s) == Intent.GREETING
