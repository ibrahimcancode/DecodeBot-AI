import threading
import pytest
import os
import sys
import time
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _no_real_sleep():
    with patch("time.sleep") as mock:
        yield mock


class TestAnimatedPrint:
    def test_animated_print_disabled_prints_immediately(self):
        from decodebot.utils.animations import animated_print
        with patch("builtins.print") as mock_print:
            animated_print("hello", enabled=False)
            mock_print.assert_called_once_with("hello", end="\n", flush=True)

    def test_animated_print_disabled_on_non_tty(self):
        from decodebot.utils.animations import animated_print
        with patch("builtins.print") as mock_print:
            with patch("decodebot.utils.animations._is_tty", return_value=False):
                animated_print("hello", enabled=True)
                mock_print.assert_called_once_with("hello", end="\n", flush=True)

    def test_animated_print_zero_speed_disables(self):
        from decodebot.utils.animations import animated_print
        with patch("builtins.print") as mock_print:
            with patch("decodebot.utils.animations._is_tty", return_value=True):
                animated_print("hello", enabled=True, speed=0)
                mock_print.assert_called_once_with("hello", end="\n", flush=True)

    def test_animated_print_custom_end(self):
        from decodebot.utils.animations import animated_print
        with patch("builtins.print") as mock_print:
            animated_print("hello", enabled=False, end="")
            mock_print.assert_called_once_with("hello", end="", flush=True)

    def test_animated_print_uses_char_prints_when_enabled_and_tty(self):
        from decodebot.utils.animations import animated_print
        with patch("decodebot.utils.animations._is_tty", return_value=True):
            with patch("builtins.print") as mock_print:
                animated_print("ab", enabled=True, speed=0.001)
                assert mock_print.call_count == 3
                mock_print.assert_any_call("a", end="", flush=True)
                mock_print.assert_any_call("b", end="", flush=True)
                mock_print.assert_any_call(end="\n", flush=True)


class TestShowThinking:
    def test_thinking_disabled_returns_immediately(self):
        from decodebot.utils.animations import show_thinking
        done = show_thinking(enabled=False)
        assert done.is_set() is False
        assert isinstance(done, type(threading.Event()))

    def test_thinking_disabled_on_non_tty(self):
        from decodebot.utils.animations import show_thinking
        with patch("decodebot.utils.animations._is_tty", return_value=False):
            done = show_thinking(enabled=True)
            assert done.is_set() is False

    def test_thinking_returns_event_when_enabled_and_tty(self):
        from decodebot.utils.animations import show_thinking
        with patch("decodebot.utils.animations._is_tty", return_value=True):
            done = show_thinking(enabled=True)
            assert isinstance(done, threading.Event)
            done.set()

    def test_thinking_reduced_motion_uses_dot_frames(self):
        from decodebot.utils.animations import show_thinking
        from decodebot.utils.animations import REDUCED_MOTION_FRAMES
        assert REDUCED_MOTION_FRAMES == ["..."]

    def test_thinking_standard_frames_defined(self):
        from decodebot.utils.animations import THINKING_FRAMES
        assert len(THINKING_FRAMES) >= 4


class TestConfigIntegration:
    def test_animation_config_keys_present_in_defaults(self):
        from decodebot.core.config import DEFAULT_CONFIG
        assert "enable_animations" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["enable_animations"] is True
        assert "reduced_motion" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["reduced_motion"] is False
        assert "typewriter_speed" in DEFAULT_CONFIG
        assert isinstance(DEFAULT_CONFIG["typewriter_speed"], (int, float))

    def test_animation_config_schema_valid(self):
        from decodebot.core.config import CONFIG_SCHEMA
        assert CONFIG_SCHEMA["enable_animations"] is bool
        assert CONFIG_SCHEMA["reduced_motion"] is bool
        assert CONFIG_SCHEMA["typewriter_speed"] == (int, float)

    def test_no_prohibited_imports_in_animations(self):
        import ast
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "decodebot", "utils", "animations.py"
        )
        with open(path) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("tkinter")
                    assert not alias.name.startswith("PyQt")
                    assert "numpy" not in alias.name
                    assert "tensorflow" not in alias.name
                    assert "torch" not in alias.name
            if isinstance(node, ast.ImportFrom):
                if node.module and "tkinter" in node.module:
                    pytest.fail(f"Prohibited import from tkinter in animations.py")
