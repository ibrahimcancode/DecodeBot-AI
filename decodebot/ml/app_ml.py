"""Machine Learning Engine CLI/handler layer (FR-222-FR-232).

This module is the single bridge the Chatbot Engine uses to reach the ML
Engine. It exposes one handler per registered ML command (``train``,
``predict``, ``evaluate``, ``explore``, ``models``, ``compare``, ``tune-k``)
and a ``dispatch_ml()`` router invoked by ``decodebot.core.dispatcher``.

Design constraints honored here:

- FR-222: every handler corresponds to a command registered in the same
  ``COMMANDS`` registry as the core commands.
- FR-223: raw chat input never reaches a scikit-learn ``predict`` call —
  ``handle_predict`` first parses the trailing text with ``_parse_features``
  into exactly 4 numeric values, and only parsed floats reach the model.
- FR-226: all ML settings come from the shared config (``ml_dataset``,
  ``knn_k``, ``classifier_type``, ...) with per-key defaults.
- FR-227: logging flows through the ``decodebot.ml`` logger hierarchy whose
  level is controlled by ``ml_log_level``.
- FR-228: every handler logs before recovering and returns a friendly
  message; no exception is swallowed silently.
- FR-231: the ML Engine runs without the GUI/animation layers — this module
  doubles as a standalone ``python -m decodebot.ml.app_ml`` entry point.
- FR-232: nothing here is imported at chatbot startup (the dispatcher imports
  it lazily inside the ML command branch).
"""

import logging
import re
import sys
from datetime import datetime, timezone
from functools import wraps

from decodebot.core.config import load_config
from decodebot.core.intents import Intent
from decodebot.core.session import SessionState

from .dataset import DatasetError
from .dataset_loader import load_dataset, render_explore_report
from .evaluator import EvaluationError, evaluate
from .model_manager import (
    ModelManagerError,
    compare_models,
    list_models,
    load_model,
    render_comparison_table,
    render_models_table,
    save_model,
)
from .predictor import NO_MODEL_MESSAGE, Predictor, PredictorError
from .preprocessor import PreprocessingError, preprocess_and_split
from .trainer import TrainingError, Trainer

logger = logging.getLogger(__name__)

_FEATURE_PATTERN = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)")

USAGE_MSG = "I need 4 numeric feature values to classify, e.g. " "'predict 5.1,3.5,1.4,0.2'."


def _config(session: SessionState) -> dict:
    """Return the session config, falling back to the on-disk config."""
    cfg = getattr(session, "config", None)
    if isinstance(cfg, dict) and cfg:
        return cfg
    return load_config()


def _parse_features(raw: str | None) -> list[float] | None:
    """Extract exactly 4 numeric feature values from a text tail (FR-223).

    Only the numeric tokens are used; any surrounding prose is ignored.
    Returns None when the text does not contain exactly four numbers so the
    caller can prompt the user instead of sending junk to the model.
    """
    if not raw:
        return None
    matches = _FEATURE_PATTERN.findall(raw)
    if len(matches) != 4:
        return None
    return [float(value) for value in matches]


def _friendly(func):
    """Wrap a handler so it logs and returns a friendly message on failure.

    Every ML command surfaces errors exactly like the rest of the app: the
    exception is logged (never swallowed) and the user receives a friendly
    line instead of a crash (FR-228).
    """

    @wraps(func)
    def wrapper(session, *args, **kwargs):
        try:
            return func(session, *args, **kwargs)
        except (
            DatasetError,
            PredictorError,
            TrainingError,
            EvaluationError,
            PreprocessingError,
            ModelManagerError,
        ) as exc:
            logger.error("ML command '%s' failed: %s", func.__name__, exc)
            return f"ML error: {exc}"
        except Exception:
            logger.exception("Unexpected failure in ML command '%s'.", func.__name__)
            return (
                "ML error: something went wrong in the Machine Learning Engine "
                "\u2014 check the logs."
            )

    return wrapper


def _ensure_pipeline(session: SessionState) -> dict:
    """Load, preprocess, train, and evaluate once; cache in session.ml_state."""
    state = session.ml_state
    if "split" in state:
        return state
    cfg = _config(session)
    dataset = load_dataset(
        cfg.get("ml_dataset", "iris"),
        cfg.get("ml_target_column"),
        use_cache=False,
    )
    split = preprocess_and_split(
        dataset,
        scaler_type=cfg.get("scaler_type", "standard"),
        test_size=cfg.get("ml_test_size", 0.2),
        random_state=cfg.get("ml_random_state", 42),
    )
    training = Trainer(
        classifier_type=cfg.get("classifier_type", "knn"),
        knn_k=int(cfg.get("knn_k", 5)),
        random_state=cfg.get("ml_random_state", 42),
    ).train(split.X_train, split.y_train)
    report = evaluate(
        training.model,
        split.X_test,
        split.y_test,
        class_names=dataset.target_names,
    )
    state.update(dataset=dataset, split=split, training=training, report=report)
    logger.info(
        "ML pipeline ready: %s with %s on %d samples.",
        training.classifier_type,
        cfg.get("ml_dataset", "iris"),
        training.n_samples,
    )
    return state


def _current_model(session: SessionState):
    """Return (model, split, dataset) or (None, None, None) (FR-199).

    Prefers the model trained earlier in this session; otherwise falls back
    to the most recently saved model in ``models_dir``.
    """
    state = session.ml_state
    if state.get("training") is not None:
        return state["training"].model, state["split"], state["dataset"]

    cfg = _config(session)
    models_dir = cfg.get("models_dir", "models/")
    infos = list_models(models_dir=models_dir)
    if not infos:
        return None, None, None
    latest = max(infos, key=lambda info: info.metadata.get("saved_at", ""))
    model = load_model(latest.name, models_dir=models_dir)
    dataset = load_dataset(
        cfg.get("ml_dataset", "iris"),
        cfg.get("ml_target_column"),
        use_cache=False,
    )
    split = preprocess_and_split(
        dataset,
        scaler_type=cfg.get("scaler_type", "standard"),
        test_size=cfg.get("ml_test_size", 0.2),
        random_state=cfg.get("ml_random_state", 42),
    )
    return model, split, dataset


@_friendly
def handle_explore(session: SessionState) -> str:
    """``explore`` — print the dataset understanding report (FR-172)."""
    cfg = _config(session)
    dataset = load_dataset(
        cfg.get("ml_dataset", "iris"),
        cfg.get("ml_target_column"),
        use_cache=False,
    )
    return render_explore_report(dataset)


@_friendly
def handle_train(session: SessionState) -> str:
    """``train`` — train, evaluate, and persist the configured model (FR-189)."""
    st = _ensure_pipeline(session)
    cfg = _config(session)
    training = st["training"]
    dataset = st["dataset"]
    path = save_model(
        training.model,
        f"{training.classifier_type}_{dataset.source}",
        models_dir=cfg.get("models_dir", "models/"),
        metadata={
            "classifier_type": training.classifier_type,
            "hyperparameters": training.model.get_params(),
            "dataset": cfg.get("ml_dataset", "iris"),
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "test_accuracy": st["report"].accuracy,
            "macro_f1": st["report"].macro_f1,
        },
    )
    return "\n".join(
        [
            f"Dataset: {dataset.source} "
            f"({dataset.features.shape[0]} samples, {dataset.features.shape[1]} features)",
            f"Training set: {st['split'].split_report.n_train} "
            f"| Test set: {st['split'].split_report.n_test}",
            training.summary(),
            f"Test accuracy: {st['report'].accuracy:.3f} "
            f"| Macro F1: {st['report'].macro_f1:.3f}",
            f"Saved model to {path}",
        ]
    )


@_friendly
def handle_predict(session: SessionState, features: list[float] | None = None) -> str:
    """``predict`` — classify 4 feature values (FR-196-FR-199, FR-223).

    ``features`` may be supplied explicitly (GUI form); otherwise they are
    parsed from ``session.last_input``. Only parsed numeric values are ever
    passed to the model.
    """
    model, split, dataset = _current_model(session)
    if model is None:
        return NO_MODEL_MESSAGE
    if features is None:
        features = _parse_features(getattr(session, "last_input", "") or "")
    if features is None:
        return USAGE_MSG
    predictor = Predictor(
        class_names=dataset.target_names,
        preprocessor=split.preprocessor,
    )
    result = predictor.predict_one(model, features, return_proba=True)
    if result.probabilities:
        probs = ", ".join(f"{name}: {value:.3f}" for name, value in result.probabilities.items())
        return f"Prediction: {result.label}\nProbabilities: {probs}"
    return f"Prediction: {result.label}"


@_friendly
def handle_evaluate(session: SessionState) -> str:
    """``evaluate`` — full evaluation report (accuracy + matrix + macro-F1)."""
    model, split, dataset = _current_model(session)
    if model is None:
        return NO_MODEL_MESSAGE
    report = evaluate(
        model,
        split.X_test,
        split.y_test,
        class_names=dataset.target_names,
    )
    return report.render()


@_friendly
def handle_models(session: SessionState) -> str:
    """``models`` — list saved models (FR-214)."""
    cfg = _config(session)
    return render_models_table(list_models(models_dir=cfg.get("models_dir", "models/")))


@_friendly
def handle_compare(session: SessionState) -> str:
    """``compare`` — same-split classifier comparison (FR-215)."""
    st = _ensure_pipeline(session)
    cfg = _config(session)
    report = compare_models(
        st["split"],
        random_state=int(cfg.get("ml_random_state", 42)),
        knn_k=int(cfg.get("knn_k", 5)),
        class_names=st["dataset"].target_names,
    )
    return render_comparison_table(report)


@_friendly
def handle_tune_k(session: SessionState) -> str:
    """``tune-k`` — scan K values with the elbow method (FR-190)."""
    st = _ensure_pipeline(session)
    cfg = _config(session)
    tune = Trainer(
        knn_k=int(cfg.get("knn_k", 5)),
        random_state=int(cfg.get("ml_random_state", 42)),
    ).tune_k(
        st["split"].X_train,
        st["split"].y_train,
        st["split"].X_test,
        st["split"].y_test,
    )
    scanned = ", ".join(f"K={k}: {error:.3f}" for k, error in tune.scores)
    return f"Best K: {tune.best_k} (error rate {tune.best_error_rate:.3f})\n" f"Scanned: {scanned}"


_ML_HANDLERS: dict[Intent, object] = {
    Intent.TRAIN: handle_train,
    Intent.PREDICT: handle_predict,
    Intent.EVALUATE: handle_evaluate,
    Intent.EXPLORE: handle_explore,
    Intent.MODELS: handle_models,
    Intent.COMPARE: handle_compare,
    Intent.TUNE_K: handle_tune_k,
}


def dispatch_ml(intent: Intent, session: SessionState) -> str:
    """Route an ML intent to its handler (invoked by the core dispatcher)."""
    handler = _ML_HANDLERS.get(intent)
    if handler is None:
        logger.warning("No ML handler registered for intent %s.", intent)
        return "ML error: unknown ML command."
    return handler(session)


def main(argv: list[str] | None = None) -> int:
    """Standalone ML CLI entry point — no GUI, no animations (FR-231)."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print(
            "Usage: python -m decodebot.ml.app_ml "
            "<train|predict|evaluate|explore|models|compare|tune-k> [values...]"
        )
        return 2

    command = argv[0].lower()
    session = SessionState()
    session.config = load_config()
    session.last_input = " ".join(argv)

    intent_by_name: dict[str, Intent] = {}
    for intent in _ML_HANDLERS:
        intent_by_name[intent.name.lower()] = intent
        intent_by_name[intent.name.lower().replace("_", "-")] = intent
    intent = intent_by_name.get(command)
    if intent is None:
        print(f"Unknown ML command: {command}")
        return 2
    print(dispatch_ml(intent, session))
    return 0


if __name__ == "__main__":
    sys.exit(main())
