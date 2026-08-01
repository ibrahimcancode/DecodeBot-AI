"""Phase 21 — GUI ML tab tests (FR-224, FR-225).

Verifies that the "Machine Learning" tab exists (FR-224), its buttons bind to
the exact CLI ML functions, and the predict form forwards four numeric values
through the identical classification path (FR-225). Also asserts the GUI
never imports an ML library (FR-229).
"""

import ast
import os
from unittest.mock import patch

import pytest

from decodebot.core.session import SessionState

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ml_session(tmp_path):
    session = SessionState()
    session.config = {
        "ml_dataset": "iris",
        "ml_target_column": None,
        "ml_test_size": 0.2,
        "ml_random_state": 42,
        "knn_k": 5,
        "classifier_type": "knn",
        "scaler_type": "standard",
        "ml_missing_value_strategy": "error",
        "models_dir": str(tmp_path),
        "ml_outputs_dir": str(tmp_path),
        "ml_log_level": "INFO",
    }
    return session


class TestFr224TabWiring:
    def test_app_gui_has_ml_tab(self):
        path = os.path.join(PROJECT_ROOT, "decodebot", "gui", "app_gui.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert 'text="Machine Learning"' in source
        assert "ttk.Notebook" in source
        assert "_build_ml_panel(" in source

    def test_ml_handlers_expose_all_commands(self, tmp_path):
        from decodebot.gui.app_gui import _ml_handlers

        session = _ml_session(tmp_path)
        handlers = _ml_handlers(session)
        for key in ("train", "predict", "evaluate", "explore", "models", "compare", "tune_k"):
            assert key in handlers
            assert callable(handlers[key])

    def test_ml_handlers_use_same_functions(self, tmp_path):
        """FR-224: the tab binds the identical CLI functions, not reimplementations."""
        from decodebot.gui.app_gui import _ml_handlers
        from decodebot.ml import app_ml

        session = _ml_session(tmp_path)
        handlers = _ml_handlers(session)
        with patch.object(app_ml, "handle_train") as mock_train:
            handlers["train"]()
            mock_train.assert_called_once_with(session)
        with patch.object(app_ml, "handle_predict") as mock_predict:
            handlers["predict"]([5.1, 3.5, 1.4, 0.2])
            mock_predict.assert_called_once_with(session, features=[5.1, 3.5, 1.4, 0.2])
        with patch.object(app_ml, "handle_compare") as mock_compare:
            handlers["compare"]()
            mock_compare.assert_called_once_with(session)

    def test_ml_handlers_run_pipeline(self, tmp_path):
        """Real end-to-end through the GUI-bound handlers."""
        from decodebot.gui.app_gui import _ml_handlers

        session = _ml_session(tmp_path)
        handlers = _ml_handlers(session)
        train_out = handlers["train"]()
        assert "Saved model to" in train_out
        pred_out = handlers["predict"]([5.1, 3.5, 1.4, 0.2])
        assert "setosa" in pred_out


class TestFr225PredictForm:
    def test_ml_panel_has_four_feature_entries(self):
        path = os.path.join(PROJECT_ROOT, "decodebot", "gui", "ml_panel.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "Feature values:" in source
        assert "Classify" in source

    def test_ml_panel_no_ml_imports(self):
        """FR-229: the GUI panel imports only tkinter."""
        path = os.path.join(PROJECT_ROOT, "decodebot", "gui", "ml_panel.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        prohibited = ("sklearn", "numpy", "pandas", "matplotlib", "joblib")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for p in prohibited:
                        assert not (
                            alias.name == p or alias.name.startswith(p + ".")
                        ), f"ML library '{alias.name}' imported in ml_panel.py"
            if isinstance(node, ast.ImportFrom) and node.module:
                for p in prohibited:
                    assert not (
                        node.module == p or node.module.startswith(p + ".")
                    ), f"ML library '{node.module}' imported in ml_panel.py"


class TestMlPanelWidgets:
    def test_ml_panel_builds_widget_tree(self):
        has_display = _has_display()
        if not has_display:
            pytest.skip("no display available for widget construction test")
        import tkinter as tk

        from decodebot.gui.ml_panel import MLPanel

        root = tk.Tk()
        root.withdraw()
        try:
            panel = MLPanel(root, handlers={})
            assert panel.output is not None
            assert len(panel.entries) == 4
        finally:
            root.destroy()

    def test_predict_form_rejects_non_numeric_input(self):
        """FR-225 negative: non-numeric GUI entries get a friendly message."""
        has_display = _has_display()
        if not has_display:
            pytest.skip("no display available for widget construction test")
        import tkinter as tk

        from decodebot.gui.ml_panel import MLPanel

        root = tk.Tk()
        root.withdraw()
        try:
            panel = MLPanel(root, handlers={})
            for entry, text in zip(panel.entries, ["5.1", "abc", "1.4", "0.2"]):
                entry.insert(0, text)
            panel._classify()
            text = panel.output.get("1.0", "end")
            assert "numeric values in all 4 feature fields" in text
        finally:
            root.destroy()

    def test_predict_form_accepts_numeric_input(self):
        """FR-225: valid numeric entries forward to the predict handler."""
        has_display = _has_display()
        if not has_display:
            pytest.skip("no display available for widget construction test")
        import tkinter as tk

        from decodebot.gui.ml_panel import MLPanel

        root = tk.Tk()
        root.withdraw()
        try:
            seen = []

            def fake_predict(values):
                seen.append(values)
                return "ok"

            panel = MLPanel(root, handlers={"predict": fake_predict})
            for entry, text in zip(panel.entries, ["5.1", "3.5", "1.4", "0.2"]):
                entry.insert(0, text)
            panel._classify()
            assert seen == [[5.1, 3.5, 1.4, 0.2]]
        finally:
            root.destroy()


def _has_display() -> bool:
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False
