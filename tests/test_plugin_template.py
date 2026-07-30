import importlib
import os
import sys
import tempfile
import textwrap
from unittest.mock import patch


class TestPluginInterface:
    def _sample_plugin_code(self):
        return textwrap.dedent("""\
        from decodebot.core.intents import Intent

        PATTERNS = ["thanks", "thank you", "ty"]
        INTENT = Intent.EASTER_EGG
        RESPONSES = ["You're welcome!", "Anytime!", "Glad to help!"]
        PRIORITY = 50

        def matches(normalized_text):
            import re
            for p in PATTERNS:
                if re.search(r"\\b" + re.escape(p) + r"\\b", normalized_text):
                    return True
            return False
        """)

    def test_plugin_matches_import_structure(self):
        plugin_code = self._sample_plugin_code()
        with tempfile.TemporaryDirectory() as tmp:
            plugin_path = os.path.join(tmp, "thanks_plugin.py")
            with open(plugin_path, "w") as f:
                f.write(plugin_code)
            sys.path.insert(0, tmp)
            try:
                mod = importlib.import_module("thanks_plugin")
                assert hasattr(mod, "PATTERNS")
                assert isinstance(mod.PATTERNS, list)
                assert hasattr(mod, "INTENT")
                assert hasattr(mod, "RESPONSES")
                assert isinstance(mod.RESPONSES, list)
                assert hasattr(mod, "PRIORITY")
                assert isinstance(mod.PRIORITY, int)
                assert hasattr(mod, "matches")
                assert callable(mod.matches)
                assert mod.matches("thanks") is True
                assert mod.matches("thank you") is True
                assert mod.matches("hello") is False
            finally:
                sys.path.pop(0)

    def test_plugin_responds_via_responder(self):
        plugin_code = self._sample_plugin_code()
        with tempfile.TemporaryDirectory() as tmp:
            plugin_path = os.path.join(tmp, "thanks_plugin.py")
            with open(plugin_path, "w") as f:
                f.write(plugin_code)
            sys.path.insert(0, tmp)
            try:
                mod = importlib.import_module("thanks_plugin")
                from decodebot.core.responder import get_response
                from decodebot.core.session import SessionState
                session = SessionState()
                from decodebot.core.intents import Intent
                resp = get_response(Intent.EASTER_EGG, session)
                assert isinstance(resp, str)
                assert len(resp) > 0
            finally:
                sys.path.pop(0)


class TestPluginAutoDiscovery:
    def test_plugin_loaded_when_in_plugins_dir(self):
        plugin_code = textwrap.dedent("""\
        import re
        from decodebot.core.intents import Intent

        PATTERNS = ["testplugin"]
        INTENT = Intent.EASTER_EGG
        RESPONSES = ["Plugin works!"]
        PRIORITY = 10

        def matches(normalized_text):
            return "testplugin" in normalized_text
        """)

        plugins_dir = os.path.join(
            os.path.dirname(__file__), "..", "decodebot", "plugins"
        )
        plugin_path = os.path.join(plugins_dir, "_test_discovery_plugin.py")
        try:
            with open(plugin_path, "w") as f:
                f.write(plugin_code)
            import importlib
            spec = importlib.util.spec_from_file_location(
                "_test_discovery_plugin", plugin_path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert mod.matches("testplugin") is True
            assert mod.matches("other") is False
        finally:
            if os.path.isfile(plugin_path):
                os.remove(plugin_path)


class TestBrokenPluginIsolation:
    def test_broken_plugin_does_not_crash_core(self):
        bad_code = "this is not valid python \x01 garbage"
        with tempfile.TemporaryDirectory() as tmp:
            plugin_path = os.path.join(tmp, "bad_plugin.py")
            with open(plugin_path, "w") as f:
                f.write(bad_code)
            try:
                compile(bad_code, plugin_path, "exec")
                assert False, "Should have raised SyntaxError"
            except SyntaxError:
                pass

    def test_core_intacts_after_bad_plugin_attempt(self):
        from decodebot.core.intents import Intent
        from decodebot.core.session import SessionState
        session = SessionState()
        from decodebot.core.rule_engine import classify_intent
        result = classify_intent("hello", session)
        assert result == Intent.GREETING


class TestPluginConstraints:
    def test_plugin_has_no_network_calls(self):
        plugin_code = textwrap.dedent("""\
        import urllib.request
        import os
        """)
        assert "urllib" in plugin_code

    def test_plugin_has_no_ml_deps(self):
        plugin_code = textwrap.dedent("""\
        import numpy
        import tensorflow
        import torch
        import sklearn
        """)
        prohibited = ["numpy", "tensorflow", "torch", "sklearn"]
        for pkg in prohibited:
            assert pkg in plugin_code
