import pytest

from decodebot.core.intents import Intent
from decodebot.core.session import SessionState
from decodebot.core.rule_engine import classify_intent
from decodebot.rules.help_about_version import COMMANDS, ALIASES


class TestHelpCommand:
    def test_help_classification(self):
        session = SessionState()
        assert classify_intent("help", session) == Intent.HELP

    def test_help_alias_question_mark(self):
        session = SessionState()
        assert classify_intent("?", session) == Intent.HELP

    def test_help_alias_commands(self):
        session = SessionState()
        assert classify_intent("commands", session) == Intent.HELP

    def test_help_text_contains_commands(self):
        from decodebot.rules.help_about_version import get_help_text
        text = get_help_text()
        for cmd in COMMANDS:
            assert cmd in text, f"Help text should contain '{cmd}'"

    def test_help_case_insensitive(self):
        session = SessionState()
        assert classify_intent("HELP", session) == Intent.HELP
        assert classify_intent("Help", session) == Intent.HELP


class TestAboutCommand:
    def test_about_classification(self):
        session = SessionState()
        assert classify_intent("about", session) == Intent.ABOUT

    def test_about_alias_info(self):
        session = SessionState()
        assert classify_intent("info", session) == Intent.ABOUT

    def test_about_text_mentions_decodebot(self):
        from decodebot.rules.help_about_version import get_about_text
        text = get_about_text()
        assert "DecodeBot" in text
        assert "rule-based" in text

    def test_about_who_are_you(self):
        session = SessionState()
        assert classify_intent("who are you", session) == Intent.ABOUT

    def test_about_what_are_you(self):
        session = SessionState()
        assert classify_intent("what are you", session) == Intent.ABOUT


class TestVersionCommand:
    def test_version_classification(self):
        session = SessionState()
        assert classify_intent("version", session) == Intent.VERSION

    def test_version_alias_v(self):
        session = SessionState()
        assert classify_intent("v", session) == Intent.VERSION

    def test_version_alias_dash_dash_version(self):
        session = SessionState()
        assert classify_intent("--version", session) == Intent.VERSION

    def test_version_matches_init(self):
        from decodebot.rules.help_about_version import get_version_text
        from decodebot import __version__
        text = get_version_text()
        assert __version__ in text


class TestAliasesConsistency:
    def test_all_aliases_resolve(self):
        session = SessionState()
        known_canonicals = {v[1] for v in COMMANDS.values()}
        for alias, canonical in ALIASES.items():
            intent = classify_intent(alias, session)
            assert canonical in COMMANDS, f"Alias '{alias}' -> unknown canonical '{canonical}'"

    def test_command_registry_nonempty(self):
        assert len(COMMANDS) >= 8


class TestHistoryCommand:
    def test_history_classification(self):
        session = SessionState()
        assert classify_intent("history", session) == Intent.HISTORY

    def test_history_alias_log(self):
        session = SessionState()
        assert classify_intent("log", session) == Intent.HISTORY


class TestStatsCommand:
    def test_stats_classification(self):
        session = SessionState()
        assert classify_intent("stats", session) == Intent.STATS

    def test_stats_alias_statistics(self):
        session = SessionState()
        assert classify_intent("statistics", session) == Intent.STATS


class TestResetCommand:
    def test_reset_classification(self):
        session = SessionState()
        assert classify_intent("reset", session) == Intent.RESET

    def test_reset_alias_restart(self):
        session = SessionState()
        assert classify_intent("restart", session) == Intent.RESET


class TestClearCommand:
    def test_clear_classification(self):
        session = SessionState()
        assert classify_intent("clear", session) == Intent.CLEAR

    def test_clear_alias_cls(self):
        session = SessionState()
        assert classify_intent("cls", session) == Intent.CLEAR
