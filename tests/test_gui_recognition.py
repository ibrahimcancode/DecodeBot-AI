"""GUI Recognition tab tests (W4-M5, FR-260).

All tests are headless-safe: they never create a real ``Tk`` root. Parity is
verified by routing the exact CLI engine function through the same handler the
GUI injects, and the wiring file ``app_gui.py`` is checked to register the tab
without importing the recognition engine at module scope (FR-249, FR-250).

Reference: SPEC.md Part IV — FR-260.
"""

import ast
import os
import subprocess
import sys

from decodebot.core.config import DEFAULT_CONFIG
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.session import SessionState
from decodebot.rules.help_about_version import get_help_text

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_IMAGE = os.path.join(PROJECT_ROOT, "samples", "sample_text.png")


def _session_with_config():
    session = SessionState()
    session.config = dict(DEFAULT_CONFIG)
    session.last_input = 'recognize --image "samples/sample_text.png" --psm 6'
    return session


class TestParityWithCli:
    """GUI handler output must equal the CLI dispatcher output (FR-260)."""

    def test_gui_handler_matches_cli_output(self):
        from decodebot.gui.app_gui import _recognize_handlers

        session = _session_with_config()
        cli_text = dispatch(Intent.RECOGNIZE, session)
        gui_text = _recognize_handlers(session)["recognize"](FIXTURE_IMAGE, psm=6)
        assert gui_text == cli_text

    def test_gui_handler_matches_plain_mode_cli(self):
        from decodebot.gui.app_gui import _recognize_handlers

        session = _session_with_config()
        session.config["plain_mode"] = True
        cli_text = dispatch(Intent.RECOGNIZE, session)
        gui_text = _recognize_handlers(session)["recognize"](FIXTURE_IMAGE, psm=6)
        assert gui_text == cli_text
        assert "\u250c" not in gui_text

    def test_gui_handler_stays_friendly_without_binary(self):
        from decodebot.gui.app_gui import _recognize_handlers

        session = _session_with_config()
        text = _recognize_handlers(session)["recognize"](FIXTURE_IMAGE, psm=6)
        assert "Traceback" not in text


class TestPanelValidation:
    """Inline empty-entry validation must not require a display (FR-260)."""

    def test_missing_image_message_is_friendly(self):
        from decodebot.gui.recognition_panel import MISSING_IMAGE_MESSAGE

        assert "image" in MISSING_IMAGE_MESSAGE.lower()
        assert "please" in MISSING_IMAGE_MESSAGE.lower()


class TestPanelCompliance:
    """The Recognition GUI panel must import only stdlib (FR-229, FR-260)."""

    def test_panel_imports_only_stdlib(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "decodebot", "gui", "recognition_panel.py"
        )
        with open(path) as handle:
            tree = ast.parse(handle.read())
        prohibited = [
            "numpy",
            "cv2",
            "pytesseract",
            "pandas",
            "sklearn",
            "matplotlib",
            "spacy",
            "nltk",
            "transformers",
            "langchain",
            "openai",
            "anthropic",
            "joblib",
            "decodebot.recognition",
            "decodebot.ml",
            "decodebot.recommender",
            "decodebot.core",
        ]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for name in prohibited:
                        assert not (
                            alias.name == name or alias.name.startswith(name + ".")
                        ), f"Prohibited import '{alias.name}' in GUI recognition panel"
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for name in prohibited:
                        assert not (
                            node.module == name or node.module.startswith(name + ".")
                        ), f"Prohibited import '{node.module}' in GUI recognition panel"

    def test_app_gui_registers_recognition_tab(self):
        path = os.path.join(os.path.dirname(__file__), "..", "decodebot", "gui", "app_gui.py")
        with open(path) as handle:
            source = handle.read()
        assert "Recognition" in source
        assert "RecognitionPanel" in source
        assert "OCR / Recognition" in get_help_text()

    def test_importing_app_gui_does_not_import_recognition(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import decodebot.gui.app_gui; "
                "assert not any(m.startswith('decodebot.recognition') for m in sys.modules)",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_app_recognition_not_imported_by_app_recognition_wiring_at_scope(self):
        # app_gui imports the recognition engine lazily (FR-249)
        source = (
            "import sys\n"
            "import decodebot.gui.app_gui\n"
            "for m in sys.modules:\n"
            "    if m == 'decodebot.recognition' or "
            "m.startswith('decodebot.recognition.'):\n"
            "        sys.exit(1)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
