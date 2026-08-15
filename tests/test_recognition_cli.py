"""Week 4 OCR Recognition Engine — CLI, config & wiring tests (FR-251, FR-259-FR-261).

TC-OCR-009: the ``recognize`` command is registered in the shared
``COMMANDS`` registry, appears in ``help`` under an "OCR / Recognition"
section, produces a boxed summary with the expected text, and parses
``--image``/``--psm``/``--save``.

TC-OCR-012: isolation + startup gates — ``python main.py`` (chatbot-only)
starts in < 300ms with OCR deps installed-but-unused and never imports the
recognition package at startup.

The Tesseract *binary* is not on PATH in CI, so end-to-end OCR is asserted
only for the graceful-degradation path (friendly ``error`` status); a
monkeypatched missing-dependency path is the deterministic check (FR-255).

Reference: SPEC.md Part IV — FR-251, FR-259-FR-261, NFR-091-NFR-095.
"""

import os
import subprocess
import sys
import unittest.mock


from decodebot import recognition as recognition
from decodebot.core.config import CONFIG_SCHEMA, DEFAULT_CONFIG, load_config
from decodebot.core.intents import Intent
from decodebot.core.rule_engine import classify_intent
from decodebot.core.session import SessionState
from decodebot.recognition import app_recognition
from decodebot.rules.help_about_version import (
    COMMANDS,
    RECOGNIZE_COMMAND_NAMES,
    get_help_text,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_IMAGE = os.path.join(PROJECT_ROOT, "samples", "sample_text.png")

EXPECTED_RECOGNITION_KEYS = {
    "rec_image_path": "",
    "rec_psm": 6,
    "rec_confidence_threshold": 0.80,
    "rec_max_file_mb": 10,
    "rec_max_dimension": 4096,
    "rec_output_dir": "outputs/",
    "rec_overwrite": False,
}

CANONICAL_CLI = 'recognize --image "samples/sample_text.png" --psm 6'


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
    """FR-259: recognize is registered in the shared COMMANDS registry."""

    def test_recognize_registered(self):
        assert "recognize" in COMMANDS
        assert COMMANDS["recognize"][1] == Intent.RECOGNIZE

    def test_recognize_in_help_section(self):
        help_text = get_help_text()
        assert "OCR / Recognition:" in help_text
        assert "recognize" in help_text

    def test_recognize_command_name_set(self):
        assert "recognize" in RECOGNIZE_COMMAND_NAMES

    def test_recognize_intent_recognized(self):
        session = _session()
        assert classify_intent(CANONICAL_CLI, session) == Intent.RECOGNIZE

    def test_bare_recognize_intent_recognized(self):
        session = _session()
        assert classify_intent("recognize", session) == Intent.RECOGNIZE


class TestConfigKeys:
    """FR-251: seven recognition keys with defaults and schema types."""

    def test_defaults_present(self):
        for key, value in EXPECTED_RECOGNITION_KEYS.items():
            assert DEFAULT_CONFIG.get(key) == value, key

    def test_schema_types(self):
        assert CONFIG_SCHEMA["rec_image_path"] is str
        assert CONFIG_SCHEMA["rec_psm"] is int
        assert CONFIG_SCHEMA["rec_confidence_threshold"] == (int, float)
        assert CONFIG_SCHEMA["rec_max_file_mb"] == (int, float)
        assert CONFIG_SCHEMA["rec_max_dimension"] is int
        assert CONFIG_SCHEMA["rec_output_dir"] is str
        assert CONFIG_SCHEMA["rec_overwrite"] is bool

    def test_invalid_recognition_values_fall_back(self, monkeypatch, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            '{"rec_psm": "oops", "rec_confidence_threshold": "high", '
            '"rec_max_file_mb": "big", "rec_max_dimension": "wide", '
            '"rec_image_path": 5, "rec_overwrite": "maybe", '
            '"rec_output_dir": 9}',
            encoding="utf-8",
        )
        monkeypatch.setattr("decodebot.core.config.CONFIG_PATHS", [str(path)])
        config = load_config()
        for key, value in EXPECTED_RECOGNITION_KEYS.items():
            assert config[key] == value, key

    def test_valid_recognition_values_loaded(self, monkeypatch, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(
            '{"rec_psm": 11, "rec_confidence_threshold": 0.9, '
            '"rec_max_file_mb": 5, "rec_max_dimension": 2000, '
            '"rec_image_path": "scans/x.png", "rec_overwrite": true, '
            '"rec_output_dir": "out/"}',
            encoding="utf-8",
        )
        monkeypatch.setattr("decodebot.core.config.CONFIG_PATHS", [str(path)])
        config = load_config()
        assert config["rec_psm"] == 11
        assert config["rec_confidence_threshold"] == 0.9
        assert config["rec_max_file_mb"] == 5
        assert config["rec_max_dimension"] == 2000
        assert config["rec_image_path"] == "scans/x.png"
        assert config["rec_overwrite"] is True
        assert config["rec_output_dir"] == "out/"


class TestParseArgs:
    """parse_recognize_args: --image/--psm/--save + config defaults."""

    def test_image_psm_save_parsed(self):
        args = app_recognition.parse_recognize_args(
            'recognize --image "samples/x.png" --psm 7 --save'
        )
        assert args.image_path == "samples/x.png"
        assert args.psm == 7
        assert args.save is True

    def test_equals_form(self):
        args = app_recognition.parse_recognize_args("recognize --image=samples/x.png --psm=11")
        assert args.image_path == "samples/x.png"
        assert args.psm == 11

    def test_positional_image_when_no_flag(self):
        args = app_recognition.parse_recognize_args("recognize samples/x.png")
        assert args.image_path == "samples/x.png"
        assert args.psm == 6

    def test_invalid_psm_falls_back_to_default(self):
        args = app_recognition.parse_recognize_args("recognize --image x.png --psm auto")
        assert args.psm == 6

    def test_missing_image_yields_none(self):
        args = app_recognition.parse_recognize_args("recognize")
        assert args.image_path is None


class TestEngineRun:
    """recognize_image returns structured results; no raised exceptions."""

    def test_missing_image_returns_error_result(self):
        result = app_recognition.recognize_image("does/not/exist.png")
        assert result.status == recognition.STATUS_ERROR
        assert "not found" in str(result.message)
        assert "Traceback" not in str(result.message)

    def test_missing_dependency_is_friendly(self, monkeypatch):
        def boom(image, psm=6):
            raise recognition.DependencyUnavailableError(
                "The OCR engine needs the optional package 'pytesseract'..."
            )

        monkeypatch.setattr(app_recognition, "run_ocr", boom)
        result = app_recognition.recognize_image(FIXTURE_IMAGE)
        assert result.status == recognition.STATUS_ERROR
        assert "pytesseract" in str(result.message)

    def test_runtime_ocr_failure_is_friendly(self, monkeypatch):
        def boom(image, psm=6):
            raise recognition.OcrError("Tesseract ran but failed")

        monkeypatch.setattr(app_recognition, "run_ocr", boom)
        result = app_recognition.recognize_image(FIXTURE_IMAGE)
        assert result.status == recognition.STATUS_ERROR
        assert "Tesseract ran but failed" in str(result.message)

    def test_real_env_run_is_graceful(self):
        """With deps installed but no binary: friendly error, never a crash."""
        result = app_recognition.recognize_image(FIXTURE_IMAGE)
        assert isinstance(result, recognition.RecognitionResult)
        assert result.status in (
            recognition.STATUS_ERROR,
            recognition.STATUS_NO_TEXT,
            recognition.STATUS_ACCEPTED,
        )


class TestRender:
    """FR-258: boxed summary; plain mode has zero box/ANSI characters."""

    def test_accepted_result_is_boxed(self):
        words = (recognition.Word(text="hello", confidence=0.95, bbox=(0, 0, 1, 1), order=0),)
        result = recognition.build_result(
            words, image_path="samples/x.png", confidence_threshold=0.80
        )
        rendered = app_recognition.render_result(result, plain=False)
        assert "Status: Accepted" in rendered
        assert "\u250c" in rendered and "\u2518" in rendered
        assert "Words: 1" in rendered
        assert "Confidence:" in rendered

    def test_error_result_renders_message(self):
        result = recognition.error_result("Tesseract OCR is not installed...", image_path="x.png")
        rendered = app_recognition.render_result(result, plain=False)
        assert "Tesseract OCR is not installed" in rendered

    def test_plain_mode_has_no_box_chars(self):
        words = (recognition.Word(text="ok", confidence=0.95, bbox=(0, 0, 1, 1), order=0),)
        result = recognition.build_result(words, image_path="x.png")
        rendered = app_recognition.render_result(result, plain=True)
        assert "\u250c" not in rendered and "\u2518" not in rendered
        assert "\x1b" not in rendered
        assert "Status: Accepted" in rendered


class TestMainDispatch:
    """FR-259: python main.py recognize dispatch + usage message."""

    def test_missing_image_usage_and_exit_code(self, monkeypatch, capfd):
        monkeypatch.setattr(sys, "argv", ["main.py", "recognize"])
        code = app_recognition.main()
        assert code == 2
        out = capfd.readouterr().out
        assert "--image" in out
        assert "Traceback" not in out

    def test_fixture_run_via_main_is_friendly(self, monkeypatch, capfd):
        monkeypatch.setattr(
            sys, "argv", ["main.py", "recognize", "--image", FIXTURE_IMAGE, "--psm", "6"]
        )
        code = app_recognition.main()
        assert code == 0
        out = capfd.readouterr().out
        assert "Traceback" not in out


class TestStartupIsolation:
    """FR-249, FR-250, NFR-091/NFR-095: chatbot unaffected by OCR being installed."""

    def test_importing_app_does_not_import_recognition(self):
        script = (
            "import sys\n"
            "import decodebot.core.app\n"
            "for m in sys.modules:\n"
            "    if m == 'decodebot.recognition' "
            "or m.startswith('decodebot.recognition.'):\n"
            "        print('IMPORTED:' + m)\n"
            "        sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout

    def test_chatbot_startup_under_300ms_with_ocr_deps_installed(self):
        script = (
            "import time\n"
            "import sys\n"
            "start = time.perf_counter()\n"
            "import decodebot.core.app\n"
            "elapsed = (time.perf_counter() - start) * 1000\n"
            "present = [m for m in ('cv2', 'pytesseract') if m in sys.modules]\n"
            "print(elapsed)\n"
            "if present or elapsed > 300:\n"
            "    sys.exit(1)\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        elapsed = float(result.stdout.strip())
        assert elapsed < 300, f"chatbot startup took {elapsed:.1f}ms (NFR-095)"

    def test_app_gui_does_not_import_recognition_module(self):
        script = (
            "import sys\n"
            "import decodebot.gui.app_gui\n"
            "for m in sys.modules:\n"
            "    if m == 'decodebot.recognition' "
            "or m.startswith('decodebot.recognition.'):\n"
            "        print('IMPORTED:' + m)\n"
            "        sys.exit(1)\n"
            "print('OK')\n"
        )
        result = _run_subprocess(script)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout


class TestRecognizedCoverage:
    """Targeted coverage for app_recognition.py success/edge paths (NFR-094)."""

    def _ok_output(self):
        return recognition.OcrOutput(
            words=(recognition.Word(text="hello", confidence=0.95, bbox=(0, 0, 1, 1), order=0),),
            full_text="hello",
            psm=6,
        )

    def test_parse_ignores_unknown_flags(self):
        args = app_recognition.parse_recognize_args("recognize --image x.png --verbose 5 --psm 7")
        assert args.image_path == "x.png"
        assert args.psm == 7
        assert args.save is False

    def test_recognize_image_unsupported_psm_is_error(self, monkeypatch):
        monkeypatch.setattr(app_recognition, "run_ocr", lambda image, psm=6: self._ok_output())
        monkeypatch.setattr(
            app_recognition,
            "preprocess_image",
            lambda image: (image, {"deskew_applied": False, "detected_angle": 0.0}),
        )
        result = app_recognition.recognize_image(FIXTURE_IMAGE, psm=1)
        assert result.status == recognition.STATUS_ERROR
        assert "Unsupported PSM" in result.message

    def test_recognize_image_success_builds_result(self, monkeypatch):
        monkeypatch.setattr(app_recognition, "run_ocr", lambda image, psm=6: self._ok_output())
        monkeypatch.setattr(
            app_recognition,
            "preprocess_image",
            lambda image: (image, {"deskew_applied": False, "detected_angle": 0.0}),
        )
        result = app_recognition.recognize_image(FIXTURE_IMAGE, psm=6)
        assert result.status == recognition.STATUS_ACCEPTED
        assert result.text == "hello"
        assert [word.text for word in result.words] == ["hello"]

    def test_recognize_image_save_writes_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(app_recognition, "run_ocr", lambda image, psm=6: self._ok_output())
        monkeypatch.setattr(
            app_recognition,
            "preprocess_image",
            lambda image: (image, {"deskew_applied": False, "detected_angle": 0.0}),
        )
        result = app_recognition.recognize_image(
            FIXTURE_IMAGE, psm=6, output_dir=str(tmp_path), save=True
        )
        assert result.saved_to is not None
        assert os.path.isfile(result.saved_to)
        assert open(result.saved_to, encoding="utf-8").read() == "hello"

    def test_handle_recognize_missing_image_returns_usage(self):
        text = app_recognition.handle_recognize(dict(DEFAULT_CONFIG), "recognize")
        assert "--image" in text

    def test_handle_recognize_plain_mode_no_box_chars(self):
        config = dict(DEFAULT_CONFIG)
        config["plain_mode"] = True
        with (
            unittest.mock.patch.object(
                app_recognition, "run_ocr", lambda image, psm=6: self._ok_output()
            ),
            unittest.mock.patch.object(
                app_recognition,
                "preprocess_image",
                lambda image: (image, {"deskew_applied": False, "detected_angle": 0.0}),
            ),
        ):
            text = app_recognition.handle_recognize(
                config, 'recognize --image "samples/sample_text.png"'
            )
        assert "\u250c" not in text
        assert "Status: Accepted" in text

    def test_render_result_with_deskew(self):
        words = (recognition.Word(text="ok", confidence=0.95, bbox=(0, 0, 1, 1), order=0),)
        result = recognition.build_result(words, deskew_applied=True, detected_angle=-2.50)
        rendered = app_recognition.render_result(result, plain=False)
        assert "Deskew: applied (-2.50\u00b0)" in rendered

    def test_recognize_to_text_loads_default_config(self, monkeypatch):
        monkeypatch.setattr(app_recognition, "run_ocr", lambda image, psm=6: self._ok_output())
        monkeypatch.setattr(
            app_recognition,
            "preprocess_image",
            lambda image: (image, {"deskew_applied": False, "detected_angle": 0.0}),
        )
        text = app_recognition.recognize_to_text(FIXTURE_IMAGE, psm=6)
        assert isinstance(text, str)
