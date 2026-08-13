"""GUI Career Recommender tab tests (W3-M5, FR-246).

All tests are headless-safe: they never create a real ``Tk`` root. Parity is
verified by routing the exact CLI engine function through the same handler the
GUI injects, and the wiring file ``app_gui.py`` is checked to register the tab
without importing the recommender at module scope (FR-233).
"""

import ast
import os
import subprocess
import sys

from decodebot.core.config import DEFAULT_CONFIG
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.session import SessionState

CANONICAL_SKILLS = "Python, SQL, Machine Learning"
CANONICAL_CMD = f'recommend --skills "{CANONICAL_SKILLS}"'


def _session_with_config():
    session = SessionState()
    session.config = dict(DEFAULT_CONFIG)
    session.last_input = CANONICAL_CMD
    return session


class TestParityWithCli:
    """GUI handler output must be byte-for-byte the CLI dispatcher output."""

    def test_gui_handler_matches_cli_output(self):
        from decodebot.gui.app_gui import _recommend_handlers

        session = _session_with_config()
        cli_text = dispatch(Intent.RECOMMEND, session)
        gui_text = _recommend_handlers(session)["recommend"](CANONICAL_SKILLS)
        assert gui_text == cli_text

    def test_gui_handler_returns_top_three_ranked(self):
        from decodebot.gui.app_gui import _recommend_handlers

        session = _session_with_config()
        text = _recommend_handlers(session)["recommend"](CANONICAL_SKILLS)
        assert "Machine Learning Engineer" in text
        assert "Data Scientist" in text
        assert "NLP Engineer" in text
        assert "1." in text

    def test_gui_handler_matches_plain_mode_cli(self):
        from decodebot.gui.app_gui import _recommend_handlers

        session = _session_with_config()
        session.config["plain_mode"] = True
        cli_text = dispatch(Intent.RECOMMEND, session)
        gui_text = _recommend_handlers(session)["recommend"](CANONICAL_SKILLS)
        assert gui_text == cli_text
        assert "\u250c" not in gui_text


class TestPanelValidation:
    """Inline empty-entry validation must not require a display (FR-246)."""

    def test_empty_skills_returns_message(self):
        from decodebot.gui.recommender_panel import validate_skills

        assert validate_skills("") is not None
        assert validate_skills("   ") is not None

    def test_blank_skills_message_is_friendly(self):
        from decodebot.gui.recommender_panel import (
            EMPTY_SKILLS_MESSAGE,
            validate_skills,
        )

        message = validate_skills("\t")
        assert message == EMPTY_SKILLS_MESSAGE
        assert "skills" in message.lower()

    def test_populated_skills_pass_validation(self):
        from decodebot.gui.recommender_panel import validate_skills

        assert validate_skills("Python") is None
        assert validate_skills("Python, SQL") is None


class TestPanelCompliance:
    def test_panel_imports_only_stdlib(self):
        import tkinter  # noqa: F401  (stdlib, safe to import headless)

        path = os.path.join(
            os.path.dirname(__file__), "..", "decodebot", "gui", "recommender_panel.py"
        )
        with open(path) as f:
            tree = ast.parse(f.read())
        prohibited = [
            "numpy",
            "tensorflow",
            "torch",
            "sklearn",
            "spacy",
            "nltk",
            "transformers",
            "langchain",
            "openai",
            "anthropic",
            "decodebot.recommender",
            "decodebot.ml",
            "decodebot.core",
        ]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for p in prohibited:
                        if alias.name == p or alias.name.startswith(p + "."):
                            pytest_fail(alias.name)
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for p in prohibited:
                        if node.module == p or node.module.startswith(p + "."):
                            pytest_fail(node.module)

    def test_app_gui_registers_recommender_tab(self):
        path = os.path.join(os.path.dirname(__file__), "..", "decodebot", "gui", "app_gui.py")
        with open(path) as f:
            source = f.read()
        assert "Career Recommender" in source
        assert "RecommenderPanel" in source

    def test_importing_app_gui_does_not_import_recommender(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import decodebot.gui.app_gui; "
                "assert not any(m.startswith('decodebot.recommender') for m in sys.modules)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def pytest_fail(name):
    import pytest

    pytest.fail(f"Prohibited import '{name}' in GUI recommender wiring")
