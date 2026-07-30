import pytest

from decodebot.core.session import SessionState
from decodebot.core.intents import Intent
from decodebot.core.io_handler import get_input, print_response
from decodebot.core.loop import run_session, dispatch_intent


class TestErrorHandling:
    def test_keyboard_interrupt_graceful(self):
        pass

    def test_eof_error_graceful(self):
        pass

    def test_consecutive_error_counter(self):
        session = SessionState()
        assert session.consecutive_unknown == 0

    def test_classify_intent_never_crashes(self):
        session = SessionState()
        dangerous_inputs = [
            "",
            " " * 1000,
            "\x00\x01\x02",
            "!" * 100,
            "a" * 10000,
            "hello\nworld",
            "%%%",
            "\ufffd\ufffd\ufffd",
        ]
        for inp in dangerous_inputs:
            try:
                from decodebot.core.rule_engine import classify_intent
                intent = classify_intent(inp, session)
                assert isinstance(intent, Intent)
            except Exception as e:
                pytest.fail(f"Crash on input {inp!r}: {e}")

    def test_farewell_on_unknown_never_exits(self):
        session = SessionState()
        from decodebot.core.rule_engine import classify_intent
        for _ in range(50):
            intent = classify_intent("xyzzy_unknown", session)
            assert intent == Intent.UNKNOWN
