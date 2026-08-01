"""Phase 21 — ML command wiring tests (FR-222, FR-223, FR-226, FR-228,
FR-231, FR-232).

Covers registration of the ML commands in the shared ``COMMANDS`` registry
(FR-222), the P0 rule that raw chat input never reaches a scikit-learn
``predict`` call (FR-223), the ML config keys with per-key validation
(FR-226), friendly error handling under malformed input (FR-228), the
standalone ML entry point (FR-231), and the lazy-import startup guarantee
(FR-232).
"""

import ast
import inspect
import logging
import os
import random
import string
import subprocess
import sys

import pytest

from decodebot.core.config import DEFAULT_CONFIG
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.rule_engine import classify_intent
from decodebot.core.session import SessionState
from decodebot.rules.help_about_version import COMMANDS, ML_COMMAND_NAMES, get_help_text
from decodebot.ml import app_ml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _parent(tree, node):
    """Return the nearest enclosing AST node of ``node`` (or None)."""
    for candidate in ast.walk(tree):
        for child in ast.iter_child_nodes(candidate):
            if child is node:
                return candidate
    return None


ML_INTENTS = frozenset(
    {
        Intent.TRAIN,
        Intent.PREDICT,
        Intent.EVALUATE,
        Intent.EXPLORE,
        Intent.MODELS,
        Intent.COMPARE,
        Intent.TUNE_K,
    }
)

EXPECTED_ML_COMMANDS = {
    "train": Intent.TRAIN,
    "predict": Intent.PREDICT,
    "evaluate": Intent.EVALUATE,
    "explore": Intent.EXPLORE,
    "models": Intent.MODELS,
    "compare": Intent.COMPARE,
    "tune-k": Intent.TUNE_K,
}

ML_KEYS = {
    "ml_dataset": "iris",
    "ml_target_column": None,
    "ml_test_size": 0.2,
    "ml_random_state": 42,
    "knn_k": 5,
    "classifier_type": "knn",
    "scaler_type": "standard",
    "ml_missing_value_strategy": "error",
    "models_dir": "models/",
    "ml_outputs_dir": "outputs/",
    "ml_log_level": "INFO",
}


def _session(tmp_path, **overrides):
    session = SessionState()
    config = {
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
    config.update(overrides)
    session.config = config
    return session


class TestFr222CommandRegistration:
    def test_ml_commands_registered_in_commands(self):
        for cmd, intent in EXPECTED_ML_COMMANDS.items():
            assert cmd in COMMANDS, f"ML command '{cmd}' missing from COMMANDS"
            assert COMMANDS[cmd][1] == intent

    def test_ml_commands_grouped_in_help(self):
        text = get_help_text()
        assert "Machine Learning:" in text
        for cmd in EXPECTED_ML_COMMANDS:
            assert cmd in text

    def test_ml_commands_classify(self):
        for cmd, intent in EXPECTED_ML_COMMANDS.items():
            session = SessionState()
            assert classify_intent(cmd, session) == intent, f"'{cmd}' did not classify"

    def test_ml_commands_case_insensitive(self):
        session = SessionState()
        assert classify_intent("TRAIN", session) == Intent.TRAIN
        assert classify_intent("Predict", session) == Intent.PREDICT

    def test_ml_command_set_matches_registry(self):
        registered = {cmd for cmd in COMMANDS if cmd in ML_COMMAND_NAMES}
        assert registered == set(EXPECTED_ML_COMMANDS)

    def test_natural_language_not_hijacked(self):
        session = SessionState()
        for text in ("how are you", "whats up", "tell me a story", "goodbye my friend"):
            intent = classify_intent(text, session)
            assert intent not in ML_INTENTS, f"'{text}' wrongly classified as ML"


class TestFr223RawInputBoundary:
    def test_parse_features_valid(self):
        assert app_ml._parse_features("predict 5.1,3.5,1.4,0.2") == [5.1, 3.5, 1.4, 0.2]
        assert app_ml._parse_features("predict 5.1 3.5 1.4 0.2") == [5.1, 3.5, 1.4, 0.2]

    def test_parse_features_rejects_wrong_count(self):
        assert app_ml._parse_features("predict 1 2 3") is None
        assert app_ml._parse_features("predict 1 2 3 4 5") is None
        assert app_ml._parse_features("predict a,b,c,d") is None
        assert app_ml._parse_features("") is None
        assert app_ml._parse_features(None) is None

    def test_predict_usage_message_on_bad_input(self, tmp_path):
        session = _session(tmp_path)
        app_ml.handle_train(session)
        session.last_input = "predict 1 2"
        result = app_ml.handle_predict(session)
        assert app_ml.USAGE_MSG in result

    def test_static_no_raw_reference_in_predict_calls(self):
        """FR-223 static gate: sklearn predict calls never receive raw text.

        Scan ``app_ml.py`` and assert that every ``predict`` / ``predict_one``
        call passes only the parsed ``features`` list — never the session,
        the raw chat input, or any text variable.
        """
        path = os.path.join(PROJECT_ROOT, "decodebot", "ml", "app_ml.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("predict", "predict_one"):
                continue
            arg_names = [arg.id for arg in node.args if isinstance(arg, ast.Name)] + [
                kw.value.id for kw in node.keywords if isinstance(kw.value, ast.Name)
            ]
            for forbidden in ("session", "raw", "last_input", "text"):
                assert forbidden not in arg_names, (
                    f"Raw input '{forbidden}' reaches a predict call in app_ml.py "
                    "(FR-223 violation)"
                )


class TestFr226ConfigKeys:
    def test_default_config_has_all_ml_keys(self):
        for key, default in ML_KEYS.items():
            assert key in DEFAULT_CONFIG, f"Missing ML config key '{key}'"
            assert DEFAULT_CONFIG[key] == default

    def test_ml_target_column_defaults_to_none(self):
        assert DEFAULT_CONFIG["ml_target_column"] is None

    def test_classifier_type_valid_values(self):
        from decodebot.ml.trainer import CLASSIFIER_TYPES

        assert DEFAULT_CONFIG["classifier_type"] in CLASSIFIER_TYPES

    def test_scaler_type_valid_values(self):
        from decodebot.ml.preprocessor import SCALER_TYPES

        assert DEFAULT_CONFIG["scaler_type"] in SCALER_TYPES


class TestFr228FriendlyErrors:
    @pytest.mark.parametrize(
        "bad_config",
        [
            {"knn_k": -1},
            {"knn_k": "abc"},
            {"ml_test_size": 2.0},
            {"ml_test_size": -0.5},
            {"ml_dataset": "does_not_exist.csv", "ml_target_column": "class"},
            {"ml_random_state": "x"},
        ],
    )
    def test_malformed_config_returns_friendly_message(self, tmp_path, bad_config):
        session = _session(tmp_path, **bad_config)
        session.last_input = "predict 5.1 3.5 1.4 0.2"
        for key in ("explore", "train", "evaluate", "predict", "models", "compare", "tune_k"):
            handler = getattr(app_ml, f"handle_{key}")
            result = handler(session)
            assert isinstance(result, str)
            assert result, f"handle_{key} returned empty output"

    def test_handlers_log_before_recovering(self, tmp_path, caplog):
        session = _session(tmp_path, ml_dataset="does_not_exist.csv", ml_target_column="class")
        with caplog.at_level(logging.ERROR, logger="decodebot.ml"):
            result = app_ml.handle_train(session)
        assert result.startswith("ML error:")
        assert any(
            "failed" in record.message and record.levelno >= logging.ERROR
            for record in caplog.records
        )

    def test_fuzz_classify_intent_no_exceptions(self):
        rng = random.Random(42)
        words = [
            "train",
            "predict",
            "evaluate",
            "explore",
            "models",
            "compare",
            "tune-k",
            "help",
            "hello",
            "please",
            "the",
            "what",
            "is",
            "5.1",
            "3.5",
            "1.4",
            "0.2",
            ",",
            ".",
            "?",
            "!!",
            "quit",
            "version",
        ]
        session = SessionState()
        for _ in range(1000):
            text = " ".join(rng.choice(words) for _ in range(rng.randint(1, 6)))
            classify_intent(text, session)

    def test_fuzz_malformed_predict_text_no_exceptions(self, tmp_path):
        session = _session(tmp_path)
        app_ml.handle_train(session)
        rng = random.Random(7)
        alphabet = string.ascii_letters + string.digits + " ,.-?!"
        for _ in range(200):
            session.last_input = "predict " + "".join(
                rng.choice(alphabet) for _ in range(rng.randint(0, 30))
            )
            result = app_ml.handle_predict(session)
            assert isinstance(result, str)


class TestEdgeHandlers:
    def test_config_falls_back_to_disk_when_session_has_none(self):
        """FR-226 edge: a session without a config falls back to config.json."""
        session = SessionState()
        assert getattr(session, "config", None) is None
        out = app_ml.handle_explore(session)
        assert "Dataset: iris" in out

    def test_current_model_falls_back_to_saved_latest(self, tmp_path):
        """FR-199 edge: predict works from the most recently saved model."""
        first = _session(tmp_path)
        app_ml.handle_train(first)
        assert app_ml._current_model(first)[0] is not None

        fresh = _session(tmp_path)
        model, split, dataset = app_ml._current_model(fresh)
        assert model is not None
        assert split is not None
        assert dataset is not None
        session = fresh
        session.last_input = "predict 5.1,3.5,1.4,0.2"
        out = app_ml.handle_predict(session)
        assert "setosa" in out

    def test_current_model_empty_models_dir_returns_none(self, tmp_path):
        """FR-199 edge: no saved models and no session model -> None triple."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        session = _session(tmp_path, models_dir=str(empty_dir))
        assert app_ml._current_model(session) == (None, None, None)

    def test_predict_without_probabilities_omits_proba_line(self, tmp_path):
        """FR-198 edge: classifiers without predict_proba omit the proba line."""
        from decodebot.ml.dataset_loader import load_dataset
        from decodebot.ml.preprocessor import preprocess_and_split
        from decodebot.ml.trainer import Trainer

        session = _session(tmp_path)
        dataset = load_dataset("iris", use_cache=False)
        split = preprocess_and_split(dataset, random_state=42)
        training = Trainer(classifier_type="svm", random_state=42).train(
            split.X_train, split.y_train
        )
        session.ml_state.update(dataset=dataset, split=split, training=training)
        session.last_input = "predict 5.1,3.5,1.4,0.2"
        out = app_ml.handle_predict(session)
        assert out.startswith("Prediction:")
        assert "Probabilities" not in out

    def test_dispatch_ml_unknown_intent_warns_and_recovers(self, caplog):
        """FR-228 edge: an unmapped intent logs a warning and recovers."""
        session = SessionState()
        with caplog.at_level(logging.WARNING, logger="decodebot.ml"):
            out = app_ml.dispatch_ml(Intent.HELP, session)
        assert out == "ML error: unknown ML command."
        assert any("No ML handler" in record.message for record in caplog.records)


class TestFr231StandaloneEntry:
    def test_main_explore_returns_zero(self, capsys):
        code = app_ml.main(["explore"])
        out = capsys.readouterr().out
        assert code == 0
        assert "Dataset: iris" in out

    def test_main_no_args_returns_usage(self, capsys):
        code = app_ml.main([])
        assert code == 2
        assert "Usage:" in capsys.readouterr().out

    def test_main_unknown_command(self, capsys):
        code = app_ml.main(["frobnicate"])
        assert code == 2
        assert "Unknown ML command" in capsys.readouterr().out

    def test_main_defaults_to_sys_argv(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["decodebot.ml.app_ml"])
        assert app_ml.main() == 2
        assert "Usage:" in capsys.readouterr().out

    def test_main_predict_with_features(self, capsys):
        code = app_ml.main(["train"])
        assert code == 0
        capsys.readouterr()

    def test_main_tune_k_hyphenated_command(self, capsys):
        """FR-231 regression: the hyphenated 'tune-k' maps to TUNE_K."""
        code = app_ml.main(["tune-k"])
        out = capsys.readouterr().out
        assert code == 0
        assert "Best K" in out

    def test_main_all_commands_return_zero(self, capsys):
        """FR-231: every registered command name works via the standalone CLI."""
        for command in EXPECTED_ML_COMMANDS:
            code = app_ml.main([command])
            assert code == 0, f"standalone '{command}' failed: {capsys.readouterr().out}"
            capsys.readouterr()

    def test_main_module_runs_standalone(self):
        """FR-231: python -m decodebot.ml.app_ml works headless."""
        result = subprocess.run(
            [sys.executable, "-m", "decodebot.ml.app_ml"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2
        assert "Usage:" in result.stdout


class TestFr232LazyStartup:
    def test_startup_never_imports_ml_libraries(self):
        """FR-232: the chatbot engine imports without sklearn/numpy/joblib.

        Runs in a clean subprocess so module-level test imports cannot mask
        a startup dependency.
        """
        code = (
            "import sys; "
            "import decodebot.core.loop, decodebot.core.app, decodebot.core.dispatcher; "
            "bad = [m for m in ('sklearn','numpy','pandas','matplotlib','joblib') "
            "if m in sys.modules]; "
            "assert not bad, bad"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    def test_dispatcher_imports_ml_lazily(self):
        """The dispatcher's only ML import lives inside a function body."""
        path = os.path.join(PROJECT_ROOT, "decodebot", "core", "dispatcher.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        ml_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("decodebot.ml")
        ]
        assert ml_imports, "dispatcher should bridge to decodebot.ml"
        for node in ml_imports:
            scope = node
            while scope is not None:
                if isinstance(scope, ast.FunctionDef):
                    break
                scope = _parent(tree, scope)
            else:
                pytest.fail("ML import in dispatcher.py must be function-local (FR-232)")

    def test_predict_requires_parse_before_model(self):
        """handle_predict never sends text to the model without parsing."""
        source = inspect.getsource(app_ml.handle_predict)
        assert "_parse_features" in source
        assert "predict_one(model, features" in source


class TestEndToEndPipeline:
    def test_dispatch_through_core(self, tmp_path):
        """Full loop: classify -> dispatch -> handler output."""
        session = _session(tmp_path)
        session.last_input = "explore"
        intent = classify_intent(session.last_input, session)
        assert intent == Intent.EXPLORE
        text = dispatch(intent, session)
        assert "Dataset: iris" in text

    def test_train_predict_evaluate_flow(self, tmp_path):
        session = _session(tmp_path)
        train_text = dispatch(Intent.TRAIN, session)
        assert "Saved model to" in train_text
        assert "Test accuracy:" in train_text

        session.last_input = "predict 5.1,3.5,1.4,0.2"
        pred_text = dispatch(Intent.PREDICT, session)
        assert "setosa" in pred_text

        eval_text = dispatch(Intent.EVALUATE, session)
        assert "Confusion Matrix" in eval_text

        models_text = dispatch(Intent.MODELS, session)
        assert "Model" in models_text

    def test_predict_without_model_is_friendly(self, tmp_path):
        session = _session(tmp_path)
        session.last_input = "predict 5.1 3.5 1.4 0.2"
        text = dispatch(Intent.PREDICT, session)
        assert "No trained model" in text
