"""Wave 3, Milestone 4 — recommend CLI, config, logging & error handling.

Covers TC-REC-010 (boxed CLI output and ``--plain`` with zero box/ANSI chars),
TC-REC-011 (1,000-iteration fuzz on malformed ``recommend`` invocations with
zero unhandled exceptions, FR-247), and TC-REC-012 (startup/isolation gates:
the Chatbot Engine never imports the recommender at startup), plus the FR-239
command registration in the shared ``COMMANDS`` registry with a distinct
"Recommendations" help section and the FR-235 config keys with per-key
validation and default fallback.

Reference: SPEC.md Part III — FR-235, FR-239, FR-245, FR-247, FR-133.
"""

import os
import random
import string
import subprocess
import sys

import pytest
from unittest.mock import patch

from decodebot.core.config import CONFIG_SCHEMA, DEFAULT_CONFIG, load_config
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.rule_engine import classify_intent
from decodebot.core.session import SessionState
from decodebot.rules.help_about_version import (
    COMMANDS,
    RECOMMEND_COMMAND_NAMES,
    get_help_text,
)
from decodebot.recommender import app_recommender
from decodebot.recommender import corpus as corpus_module

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BOX_CHARS = "\u250c\u2510\u2514\u2518\u2500\u2502"
CANONICAL_INPUT = 'recommend --skills "Python, SQL, Machine Learning"'

EXPECTED_RECOMMENDER_KEYS = {
    "recommender_corpus": "builtin",
    "recommender_top_n": 3,
    "recommender_min_skills": 3,
    "recommender_threshold": 0.0,
    "recommender_random_state": 42,
}


@pytest.fixture(autouse=True)
def _clear_cache():
    corpus_module._CACHE.clear()
    yield
    corpus_module._CACHE.clear()


def _session(config=None, last_input=""):
    session = SessionState()
    session.config = dict(DEFAULT_CONFIG)
    if config:
        session.config.update(config)
    session.last_input = last_input
    return session


def _run_subprocess(script):
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


class TestCommandRegistry:
    """FR-239: recommend is registered in the shared COMMANDS registry."""

    def test_recommend_registered(self):
        assert "recommend" in COMMANDS
        assert COMMANDS["recommend"][1] == Intent.RECOMMEND

    def test_recommend_in_help_recommendations_section(self):
        help_text = get_help_text()
        assert "Recommendations:" in help_text
        assert "recommend" in help_text

    def test_recommend_command_name_set(self):
        assert "recommend" in RECOMMEND_COMMAND_NAMES

    def test_recommend_intent_recognized(self):
        session = _session()
        intent = classify_intent(CANONICAL_INPUT, session)
        assert intent == Intent.RECOMMEND

    def test_bare_recommend_intent_recognized(self):
        session = _session()
        assert classify_intent("recommend", session) == Intent.RECOMMEND


class TestConfigKeys:
    """FR-235: five recommender keys with defaults and schema types."""

    def test_defaults_present(self):
        for key, value in EXPECTED_RECOMMENDER_KEYS.items():
            assert DEFAULT_CONFIG.get(key) == value

    def test_schema_types(self):
        assert CONFIG_SCHEMA["recommender_corpus"] is str
        assert CONFIG_SCHEMA["recommender_top_n"] is int
        assert CONFIG_SCHEMA["recommender_min_skills"] is int
        assert CONFIG_SCHEMA["recommender_threshold"] == (int, float)
        assert CONFIG_SCHEMA["recommender_random_state"] is int

    def test_invalid_recommender_values_fall_back(self, monkeypatch, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            '{"recommender_top_n": "oops", "recommender_threshold": "high", '
            '"recommender_corpus": 42, "recommender_min_skills": "x", '
            '"recommender_random_state": "y"}',
            encoding="utf-8",
        )
        monkeypatch.setattr("decodebot.core.config.CONFIG_PATHS", [str(path)])
        config = load_config()
        for key, value in EXPECTED_RECOMMENDER_KEYS.items():
            assert config[key] == value

    def test_valid_recommender_values_loaded(self, monkeypatch, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            '{"recommender_top_n": 5, "recommender_threshold": 0.25, '
            '"recommender_min_skills": 2, "recommender_random_state": 7, '
            '"recommender_corpus": "custom.csv"}',
            encoding="utf-8",
        )
        monkeypatch.setattr("decodebot.core.config.CONFIG_PATHS", [str(path)])
        config = load_config()
        assert config["recommender_top_n"] == 5
        assert config["recommender_threshold"] == 0.25
        assert config["recommender_min_skills"] == 2
        assert config["recommender_random_state"] == 7
        assert config["recommender_corpus"] == "custom.csv"


class TestCliOutput:
    """TC-REC-010: boxed top-3 output; --plain has zero box/ANSI characters."""

    def test_boxed_top_three(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input=CANONICAL_INPUT))
        assert "Career Recommendations" in out
        assert "\u250c" in out and "\u2518" in out
        assert out.count("\u2502") > 3

    def test_three_ranked_rows(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input=CANONICAL_INPUT))
        for rank in ("1. ", "2. ", "3. "):
            assert rank in out

    def test_rows_show_title_percent_and_matched(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input=CANONICAL_INPUT))
        assert "%" in out
        assert "matched:" in out

    def test_no_ansi_codes_in_boxed(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input=CANONICAL_INPUT))
        assert "\x1b" not in out

    def test_plain_mode_no_box_chars(self):
        session = _session(config={"plain_mode": True}, last_input=CANONICAL_INPUT)
        out = dispatch(Intent.RECOMMEND, session)
        for char in BOX_CHARS:
            assert char not in out
        assert "\x1b" not in out
        assert "1. Machine Learning Engineer" in out

    def test_plain_mode_still_shows_all_rows(self):
        session = _session(config={"plain_mode": True}, last_input=CANONICAL_INPUT)
        out = dispatch(Intent.RECOMMEND, session)
        assert "1. " in out and "2. " in out and "3. " in out

    def test_render_outcome_plain_helper(self):
        outcome = app_recommender.build_recommendation(
            corpus_module.builtin_corpus(), "Python, SQL, Machine Learning"
        )
        text = app_recommender.render_outcome(outcome, plain=True)
        for char in BOX_CHARS:
            assert char not in text

    def test_render_outcome_boxed_helper(self):
        outcome = app_recommender.build_recommendation(
            corpus_module.builtin_corpus(), "Python, SQL, Machine Learning"
        )
        text = app_recommender.render_outcome(outcome, plain=False)
        assert "\u250c" in text

    def test_render_fallback_plain_helper(self):
        from decodebot.recommender.result import RecommendationOutcome, STATUS_GUIDANCE

        outcome = RecommendationOutcome(
            results=(),
            status=STATUS_GUIDANCE,
            message="Guidance message",
        )
        text = app_recommender.render_outcome(outcome, plain=True)
        assert text == "Guidance message"
        for char in BOX_CHARS:
            assert char not in text

    def test_render_fallback_boxed_helper(self):
        from decodebot.recommender.result import RecommendationOutcome, STATUS_ZERO_MATCH

        outcome = RecommendationOutcome(
            results=(),
            status=STATUS_ZERO_MATCH,
            message="Zero match message",
        )
        text = app_recommender.render_outcome(outcome, plain=False)
        assert "Zero match message" in text
        assert "\u250c" in text


class TestPlainFlag:
    """FR-133: --plain on the command line flips plain_mode."""

    def test_main_plain_sets_override(self):
        import sys
        from main import main

        captured = {}

        def fake_run(config_overrides=None):
            captured["overrides"] = config_overrides
            return 0

        with patch.object(sys, "argv", ["main.py", "--plain"]):
            with patch("decodebot.core.app.run", side_effect=fake_run) as mock_run:
                assert main() == 0
                mock_run.assert_called_once()
        assert captured["overrides"] == {"plain_mode": True}

    def test_main_without_plain_passes_none(self):
        import sys
        from main import main

        captured = {}

        def fake_run(config_overrides=None):
            captured["overrides"] = config_overrides
            return 0

        with patch.object(sys, "argv", ["main.py"]):
            with patch("decodebot.core.app.run", side_effect=fake_run) as mock_run:
                assert main() == 0
                mock_run.assert_called_once()
        assert captured["overrides"] is None

    def test_app_run_merges_override(self):
        from decodebot.core.app import run

        captured = {}

        def fake_run_session(config=None):
            captured["config"] = config
            return 0

        with patch("decodebot.core.app.run_session", side_effect=fake_run_session):
            run(config_overrides={"plain_mode": True})
        assert captured["config"]["plain_mode"] is True


class TestUsageGuidance:
    """FR-239 edge case: missing --skills → friendly usage, no crash."""

    def test_missing_skills_usage_message(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input="recommend"))
        assert app_recommender.USAGE_MESSAGE in out
        assert "--skills" in out

    def test_empty_skills_usage_message(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input='recommend --skills ""'))
        assert "--skills" in out

    def test_usage_is_friendly_not_stacktrace(self):
        out = dispatch(Intent.RECOMMEND, _session(last_input="recommend"))
        assert "Traceback" not in out


class TestSkillsParsing:
    def test_quoted_skills(self):
        assert (
            app_recommender._extract_skills_arg(
                'recommend --skills "Python, SQL, Machine Learning"'
            )
            == "Python, SQL, Machine Learning"
        )

    def test_equals_form(self):
        assert (
            app_recommender._extract_skills_arg("recommend --skills=Python, SQL") == "Python, SQL"
        )

    def test_single_quoted(self):
        assert (
            app_recommender._extract_skills_arg("recommend --skills 'Python, SQL'") == "Python, SQL"
        )

    def test_unquoted_rest_of_line(self):
        assert (
            app_recommender._extract_skills_arg("recommend --skills Python, SQL, ML")
            == "Python, SQL, ML"
        )

    def test_missing_flag_returns_none(self):
        assert app_recommender._extract_skills_arg("recommend") is None

    def test_empty_flag_returns_none(self):
        assert app_recommender._extract_skills_arg("recommend --skills") is None

    def test_none_raw_returns_none(self):
        assert app_recommender._extract_skills_arg(None) is None

    def test_empty_raw_returns_none(self):
        assert app_recommender._extract_skills_arg("") is None


class TestCustomCorpusViaConfig:
    """FR-237: recommender_corpus config key drives the active corpus."""

    def test_custom_corpus_used(self, tmp_path):
        path = tmp_path / "mini.csv"
        path.write_text(
            "title,skills,description\n"
            '"Quantum Specialist","Quantum, Python, SQL","Q"\n'
            '"Backend Engineer","Backend, API, SQL","B"\n'
            '"Data Analyst","Data, SQL, Excel","D"\n',
            encoding="utf-8",
        )
        session = _session(
            config={"recommender_corpus": str(path)},
            last_input=CANONICAL_INPUT,
        )
        out = dispatch(Intent.RECOMMEND, session)
        assert "Quantum Specialist" in out
        assert "Backend Engineer" in out

    def test_bad_corpus_is_friendly(self):
        session = _session(
            config={"recommender_corpus": "definitely_missing_file.csv"},
            last_input=CANONICAL_INPUT,
        )
        out = dispatch(Intent.RECOMMEND, session)
        assert "Traceback" not in out
        assert "corpus" in out.lower() or "Recommendation error" in out


class TestFuzz:
    """TC-REC-011: 1,000 malformed recommend invocations → zero exceptions."""

    def test_1000_malformed_invocations_no_crash(self, tmp_path):
        rng = random.Random(2026)
        path = tmp_path / "fuzz.csv"
        path.write_text(
            "title,skills,description\n"
            '"Alpha","Python, SQL","A"\n'
            '"Beta","Java, Go","B"\n'
            '"Gamma","ML, Data","G"\n',
            encoding="utf-8",
        )
        chunks = [
            "recommend",
            "recommend --skills",
            'recommend --skills ""',
            'recommend --skills "Python, SQL"',
            "--skills " + "".join(rng.choice(string.printable) for _ in range(60)),
            "recommend " + "".join(rng.choice(string.ascii_letters) for _ in range(40)),
            "recommend --skills=" + "".join(rng.choice(string.punctuation) for _ in range(30)),
            "recommend --skills " + "x" * 500,
        ]
        for _ in range(1000):
            raw = rng.choice(chunks)
            session = _session(
                config={"recommender_corpus": str(path)},
                last_input=raw,
            )
            try:
                result = dispatch(Intent.RECOMMEND, session)
            except Exception as exc:  # pragma: no cover - failure path
                pytest.fail(f"Unhandled exception for input {raw!r}: {exc!r}")
            assert isinstance(result, str)


class TestStartupIsolation:
    """TC-REC-012: Chatbot startup never imports the recommender (FR-234)."""

    def test_app_import_does_not_import_recommender(self):
        script = (
            "import sys\n"
            "import decodebot.core.app\n"
            "for m in sys.modules:\n"
            "    if m == 'decodebot.recommender' "
            "or m.startswith('decodebot.recommender.'):\n"
            "        print('IMPORTED:' + m)\n"
            "        sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout

    def test_app_recommender_import_has_no_ml_side_effect(self):
        script = (
            "import sys\n"
            "import decodebot.recommender.app_recommender\n"
            "present = [m for m in ('sklearn', 'numpy', 'pandas', 'matplotlib', "
            "'joblib', 'tkinter', 'decodebot.ml', 'decodebot.core') if m in sys.modules]\n"
            "if present:\n"
            "    print('PRESENT:' + ','.join(present))\n"
            "    sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
