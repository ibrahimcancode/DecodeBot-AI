import pytest

from decodebot.core.intents import Intent
from decodebot.core.session import SessionState
from decodebot.core.rule_engine import classify_intent
from decodebot.rules.easter_eggs import EASTER_EGG_TRIGGERS, EASTER_EGG_MAP


class TestEasterEggs:
    def test_joke_classification(self):
        session = SessionState()
        assert classify_intent("tell me a joke", session) == Intent.EASTER_EGG

    def test_sentient_classification(self):
        session = SessionState()
        assert classify_intent("are you sentient", session) == Intent.EASTER_EGG

    def test_alive_classification(self):
        session = SessionState()
        assert classify_intent("are you alive", session) == Intent.EASTER_EGG

    def test_konami_classification(self):
        session = SessionState()
        assert classify_intent("up up down down", session) == Intent.EASTER_EGG

    def test_joke_returns_string(self):
        from decodebot.rules.easter_eggs import get_joke
        joke = get_joke()
        assert isinstance(joke, str)
        assert len(joke) > 0

    def test_self_aware_returns_string(self):
        from decodebot.rules.easter_eggs import get_self_aware_response
        resp = get_self_aware_response()
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_hidden_from_help(self):
        from decodebot.rules.help_about_version import COMMANDS
        for trigger in EASTER_EGG_TRIGGERS:
            assert trigger not in COMMANDS, f"'{trigger}' should be hidden from help"

    def test_easter_egg_triggers_exist(self):
        assert len(EASTER_EGG_TRIGGERS) >= 3
