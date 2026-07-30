import pytest
from unittest.mock import patch


class TestGuiFallback:
    def test_gui_fallback_on_no_display(self):
        with patch("decodebot.gui.app_gui._has_display", return_value=False):
            with patch("decodebot.core.loop.run_session") as mock_run:
                mock_run.return_value = 0
                from decodebot.gui.app_gui import run_gui
                result = run_gui()
                assert result == 0


class TestGuiCompliance:
    def test_compliance_gate_unaffected(self):
        from decodebot.core.app import run
        from decodebot.core.loop import run_session
        assert callable(run)
        assert callable(run_session)

    def test_main_no_gui_uses_cli(self):
        import sys
        with patch.object(sys, "argv", ["main.py"]):
            from main import main
            with patch("decodebot.core.app.run") as mock_run:
                mock_run.return_value = 0
                result = main()
                assert result == 0
                mock_run.assert_called_once()

    def test_main_with_gui_flag(self):
        import sys
        with patch.object(sys, "argv", ["main.py", "--gui"]):
            with patch("decodebot.gui.app_gui.run_gui") as mock_gui:
                mock_gui.return_value = 0
                from main import main
                result = main()
                assert result == 0
                mock_gui.assert_called_once()


class TestGuiProhibitedImports:
    def test_no_prohibited_imports_in_gui(self):
        import ast
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..", "decodebot", "gui", "app_gui.py"
        )
        if not os.path.isfile(path):
            pytest.skip("gui/app_gui.py not found")
        with open(path) as f:
            tree = ast.parse(f.read())
        prohibited = [
            "numpy", "tensorflow", "torch", "sklearn", "spacy", "nltk",
            "transformers", "langchain", "openai", "anthropic",
        ]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for p in prohibited:
                        if alias.name == p or alias.name.startswith(p + "."):
                            pytest.fail(f"Prohibited import '{alias.name}' in app_gui.py")
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for p in prohibited:
                        if node.module == p or node.module.startswith(p + "."):
                            pytest.fail(f"Prohibited import '{node.module}' in app_gui.py")
