"""Model persistence, security, metadata, and comparison (FR-210-FR-216).

Persists trained models via ``joblib`` into a configurable ``models/``
directory, records a companion metadata ``.json`` per model (FR-213), enforces
the FR-212 security boundary on loading (restricted to ``models/`` by default,
with an explicit opt-in flag), lists saved models with their metadata
(FR-214), compares multiple classifiers on the identical train/test split
(FR-215), and selects/saves the best model by macro-F1 (FR-216).

Reference: Week 2 brief — "Model persistence" and model-card practice.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import joblib
import numpy as np

from .dataset import DatasetError
from .evaluator import evaluate
from .trainer import Trainer

logger = logging.getLogger(__name__)

MODEL_EXTENSION = ".joblib"
DEFAULT_MODELS_DIR = "models/"
DEFAULT_COMPARE_CLASSIFIERS: tuple[str, ...] = (
    "knn",
    "decision_tree",
    "logistic_regression",
)
NO_SAVED_MODELS_MESSAGE = "No saved models yet — run 'train' to create one."
LOAD_SECURITY_MESSAGE = (
    "Loading models from outside the models/ directory is blocked by default "
    "(FR-212). Pass allow_external_path=True to override."
)


class ModelManagerError(DatasetError):
    """Raised for persistence, security, or comparison failures (FR-211, FR-212)."""


@dataclass
class ModelInfo:
    """One saved model entry for the ``models`` listing (FR-213, FR-214).

    Attributes:
        name: Model name without the ``.joblib`` extension.
        path: Absolute path to the ``.joblib`` file.
        file_size_bytes: Size of the ``.joblib`` file on disk (NFR-085).
        metadata: Contents of the companion ``.json`` metadata file, or ``{}``
            when the metadata file is missing (graceful degradation).
    """

    name: str
    path: str
    file_size_bytes: int
    metadata: dict[str, object]


@dataclass
class ClassifierComparison:
    """One classifier's metrics in a comparison run (FR-215).

    Attributes:
        classifier_type: The classifier key (FR-191).
        model: The fitted scikit-learn classifier.
        accuracy: Test-set accuracy (FR-201).
        precision: Macro-averaged precision (FR-203).
        recall: Macro-averaged recall (FR-203).
        f1: Macro-averaged F1 (FR-203).
        duration_ms: Training wall-clock time in milliseconds (FR-192).
    """

    classifier_type: str
    model: object
    accuracy: float
    precision: float
    recall: float
    f1: float
    duration_ms: float


@dataclass
class ComparisonReport:
    """Side-by-side result of a ``compare_models`` run (FR-215, FR-216).

    Attributes:
        results: One ``ClassifierComparison`` per requested classifier, in
            request order, all trained and evaluated on the identical
            train/test split.
        n_test: Number of test samples every classifier was evaluated on.
    """

    results: list[ClassifierComparison]
    n_test: int

    def best(self) -> ClassifierComparison:
        """Return the classifier with the highest macro-F1 (FR-216).

        Returns:
            The top-F1 ``ClassifierComparison``.

        Raises:
            ModelManagerError: If there are no results to select from.
        """
        if not self.results:
            raise ModelManagerError("ComparisonReport contains no results to select from.")
        return max(self.results, key=lambda result: result.f1)

    def best_model(self) -> object:
        """Return the fitted model of the best classifier (FR-216)."""
        return self.best().model


def save_model(
    model,
    name: str,
    *,
    models_dir: str = DEFAULT_MODELS_DIR,
    metadata: dict[str, object] | None = None,
) -> str:
    """Save a trained model to disk via ``joblib.dump`` (FR-210, FR-213).

    Args:
        model: A predict-capable fitted object (a classifier, or a pipeline
            including the fitted preprocessing steps per FR-179).
        name: Model name; ``.joblib`` is appended automatically when missing.
            Must not contain path separators.
        models_dir: Directory for saved models (default ``"models/"``); it is
            auto-created when missing (FR-210 edge).
        metadata: Optional metadata recorded to a companion ``.json`` file
            (FR-213). ``name`` and ``saved_at`` are always recorded; any
            provided keys (e.g. ``classifier_type``, ``hyperparameters``,
            ``trained_at``, ``dataset``, ``test_accuracy``) are merged on top.

    Returns:
        The absolute path to the saved ``.joblib`` file.

    Raises:
        ModelManagerError: For an invalid name, a non-predict-capable object,
            or a serialization failure.
    """
    if not callable(getattr(model, "predict", None)):
        raise ModelManagerError(
            "Cannot save: the object is not a predict-capable model. Train a "
            "classifier first (FR-210)."
        )
    filename = _validated_filename(name)
    models_abs = _ensure_directory(models_dir)
    path = os.path.join(models_abs, filename)
    try:
        joblib.dump(model, path)
    except Exception as exc:  # pragma: no cover - joblib rarely fails to dump
        logger.error("Failed to save model to %s.", path)
        raise ModelManagerError(f"Could not save model '{name}' to disk.") from exc

    base = filename[: -len(MODEL_EXTENSION)]
    record = {"name": base, "saved_at": _now_iso()}
    if metadata:
        record.update({str(key): _json_safe(value) for key, value in metadata.items()})
    _write_metadata(models_abs, base, record)

    logger.info("Saved model '%s' to %s.", base, path)
    return path


def load_model(
    name_or_path: str,
    *,
    models_dir: str = DEFAULT_MODELS_DIR,
    allow_external_path: bool = False,
) -> object:
    """Load a previously saved model via ``joblib.load`` (FR-211, FR-212).

    Args:
        name_or_path: A model name (resolved inside ``models_dir``) or a path
            to a ``.joblib`` file.
        models_dir: Directory containing project models (default
            ``"models/"``).
        allow_external_path: When False (default), loading a file that
            resolves outside ``models_dir`` is blocked with a friendly error
            (FR-212). When True, an explicit security ``WARNING`` is logged
            and the load proceeds.

    Returns:
        The deserialized, predict-capable model object.

    Raises:
        ModelManagerError: For a missing/corrupted file, a loaded object that
            is not predict-capable, or an FR-212 boundary violation.
    """
    if not name_or_path:
        raise ModelManagerError("No model name or path given.")
    candidate = _resolve_load_path(str(name_or_path), models_dir)
    models_abs = os.path.abspath(models_dir)

    if not _is_within(candidate, models_abs):
        if not allow_external_path:
            logger.error("Blocked loading %s from outside models/ (FR-212).", candidate)
            raise ModelManagerError(LOAD_SECURITY_MESSAGE)
        logger.warning(
            "Loading model %s from outside models/ — explicit opt-in given (FR-212).",
            candidate,
        )

    if not os.path.isfile(candidate):
        raise ModelManagerError(
            f"Couldn't load model '{name_or_path}' — file not found. "
            "Check the name and try again."
        )

    try:
        model = joblib.load(candidate)
    except Exception as exc:
        logger.error("Failed to deserialize model file %s.", candidate)
        raise ModelManagerError(
            "Couldn't load that model — the file is corrupted or unreadable. "
            "Run 'train' to retrain."
        ) from exc

    if not callable(getattr(model, "predict", None)):
        raise ModelManagerError(
            "Couldn't load that model — the file does not contain a "
            "predict-capable model. Run 'train' to retrain."
        )

    logger.info("Loaded model from %s.", candidate)
    return model


def list_models(models_dir: str = DEFAULT_MODELS_DIR) -> list[ModelInfo]:
    """List every saved ``.joblib`` model with its metadata (FR-214).

    Args:
        models_dir: Directory to scan (default ``"models/"``).

    Returns:
        A sorted list of ``ModelInfo`` entries, one per ``.joblib`` file. An
        empty ``models/`` directory (or a missing one) yields ``[]``.
    """
    if not os.path.isdir(models_dir):
        return []
    infos: list[ModelInfo] = []
    for filename in sorted(os.listdir(models_dir)):
        if not filename.endswith(MODEL_EXTENSION):
            continue
        base = filename[: -len(MODEL_EXTENSION)]
        path = os.path.abspath(os.path.join(models_dir, filename))
        infos.append(
            ModelInfo(
                name=base,
                path=path,
                file_size_bytes=int(os.path.getsize(path)),
                metadata=_read_metadata(models_dir, base),
            )
        )
    return infos


def render_models_table(
    models: list[ModelInfo], *, empty_message: str = NO_SAVED_MODELS_MESSAGE
) -> str:
    """Render the ``models`` listing as a fixed-width table (FR-214).

    Args:
        models: Model entries from ``list_models``.
        empty_message: Text shown when no models exist (FR-214 AC).

    Returns:
        The table string, or ``empty_message`` when ``models`` is empty.
    """
    if not models:
        return empty_message
    rows = [_model_row(info) for info in models]
    return _format_table(("Model", "Classifier", "Test Acc", "Trained", "Size"), rows)


def compare_models(
    preprocess_result,
    *,
    classifier_types: tuple[str, ...] = DEFAULT_COMPARE_CLASSIFIERS,
    random_state: int = 42,
    knn_k: int = 5,
    class_names: list[str] | None = None,
) -> ComparisonReport:
    """Train and evaluate multiple classifiers on the identical split (FR-215).

    Args:
        preprocess_result: A ``PreprocessResult`` from ``preprocess_and_split``
            providing the shared ``X_train``/``y_train``/``X_test``/``y_test``.
        classifier_types: Classifier keys to compare (default: KNN, decision
            tree, logistic regression). Unknown keys fall back to KNN with a
            logged warning (FR-191).
        random_state: Reproducibility seed (FR-178).
        knn_k: Neighbor count for KNN (FR-188).
        class_names: Optional human-readable class names aligned to the model's
            class order (e.g. ``Dataset.target_names``).

    Returns:
        A ``ComparisonReport`` with one entry per classifier, all evaluated on
        the identical test set.
    """
    results: list[ClassifierComparison] = []
    for classifier_type in classifier_types:
        training = Trainer(
            classifier_type=classifier_type,
            knn_k=knn_k,
            random_state=random_state,
        ).train(preprocess_result.X_train, preprocess_result.y_train)
        report = evaluate(
            training.model,
            preprocess_result.X_test,
            preprocess_result.y_test,
            class_names=class_names,
        )
        results.append(
            ClassifierComparison(
                classifier_type=training.classifier_type,
                model=training.model,
                accuracy=_plain(report.accuracy),
                precision=_plain(report.macro_precision),
                recall=_plain(report.macro_recall),
                f1=_plain(report.macro_f1),
                duration_ms=training.duration_ms,
            )
        )
        logger.info(
            "Compared %s on %d test samples: accuracy=%.4f, macro-F1=%.4f.",
            training.classifier_type,
            int(preprocess_result.X_test.shape[0]),
            report.accuracy,
            report.macro_f1,
        )
    return ComparisonReport(
        results=results,
        n_test=int(preprocess_result.X_test.shape[0]),
    )


def render_comparison_table(report: ComparisonReport) -> str:
    """Render a comparison run as a side-by-side table (FR-215).

    Args:
        report: A ``ComparisonReport`` from ``compare_models``.

    Returns:
        A fixed-width table with one row per classifier; the best macro-F1
        classifier is marked with ``*`` (FR-216).
    """
    if not report.results:
        return "No classifiers were compared."
    best_type = report.best().classifier_type
    rows = []
    for result in report.results:
        name = result.classifier_type
        if result.classifier_type == best_type:
            name = f"* {name}"
        rows.append(
            (
                name,
                f"{result.accuracy:.4f}",
                f"{result.precision:.3f}",
                f"{result.recall:.3f}",
                f"{result.f1:.3f}",
                f"{result.duration_ms:.0f}ms",
            )
        )
    return _format_table(("Classifier", "Accuracy", "Precision", "Recall", "F1", "Train"), rows)


def save_best_model(
    report: ComparisonReport,
    *,
    name: str = "best_model",
    models_dir: str = DEFAULT_MODELS_DIR,
    dataset_source: str = "iris",
) -> str:
    """Save only the top-macro-F1 classifier's model (FR-216).

    Args:
        report: A ``ComparisonReport`` from ``compare_models``.
        name: Name for the saved model (default ``"best_model"``).
        models_dir: Directory for the saved model (FR-210).
        dataset_source: Dataset identifier recorded in the metadata (FR-213).

    Returns:
        The absolute path to the saved ``.joblib`` file.

    Raises:
        ModelManagerError: If the report has no results.
    """
    best = report.best()
    metadata = {
        "classifier_type": best.classifier_type,
        "hyperparameters": best.model.get_params(),
        "trained_at": _now_iso(),
        "dataset": dataset_source,
        "test_accuracy": best.accuracy,
        "macro_f1": best.f1,
    }
    logger.info("Saving best model %s (macro-F1 %.4f).", best.classifier_type, best.f1)
    return save_model(best.model, name=name, models_dir=models_dir, metadata=metadata)


def _validated_filename(name: str) -> str:
    """Validate and normalize a model name into a safe ``.joblib`` filename."""
    filename = str(name).strip()
    if not filename:
        raise ModelManagerError("Model name must not be empty.")
    if "/" in filename or "\\" in filename:
        raise ModelManagerError(
            "Model names must not contain path separators; give a plain name "
            "like 'knn_iris' (FR-212)."
        )
    if not filename.endswith(MODEL_EXTENSION):
        filename += MODEL_EXTENSION
    return filename


def _resolve_load_path(name_or_path: str, models_dir: str) -> str:
    """Resolve a load argument to an absolute path (FR-211, FR-212).

    A plain name (no path separators, not absolute) resolves inside
    ``models_dir`` even when it already carries the ``.joblib`` suffix; any
    real path — absolute or relative — resolves as given and is subject to the
    FR-212 boundary check.
    """
    raw = os.path.normpath(name_or_path)
    if os.path.isabs(raw) or "/" in raw or "\\" in raw:
        return os.path.abspath(raw)
    if raw.endswith(MODEL_EXTENSION):
        return os.path.abspath(os.path.join(models_dir, raw))
    return os.path.abspath(os.path.join(models_dir, raw + MODEL_EXTENSION))


def _is_within(child_abs: str, parent_abs: str) -> bool:
    """Return True when ``child_abs`` is inside ``parent_abs`` (FR-212)."""
    child = os.path.normcase(os.path.abspath(child_abs))
    parent = os.path.normcase(os.path.abspath(parent_abs))
    return child == parent or child.startswith(parent + os.sep)


def _ensure_directory(models_dir: str) -> str:
    """Create and return the absolute models directory (FR-210 edge)."""
    models_abs = os.path.abspath(models_dir)
    os.makedirs(models_abs, exist_ok=True)
    return models_abs


def _write_metadata(models_dir: str, base: str, record: dict[str, object]) -> None:
    """Write the companion metadata ``.json`` next to a model (FR-213)."""
    path = os.path.join(models_dir, base + ".json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False)


def _read_metadata(models_dir: str, base: str) -> dict[str, object]:
    """Read a model's companion metadata, tolerating a missing/corrupt file."""
    path = os.path.join(models_dir, base + ".json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        logger.warning("Could not read metadata file %s.", path)
        return {}


def _model_row(info: ModelInfo) -> tuple[str, str, str, str, str]:
    """Build one table row from a ``ModelInfo`` entry (FR-214)."""
    meta = info.metadata
    classifier = str(meta.get("classifier_type", "")) or "?"
    accuracy = meta.get("test_accuracy")
    if isinstance(accuracy, (int, float)):
        accuracy_text = f"{float(accuracy):.4f}"
    else:
        accuracy_text = "?"
    trained = meta.get("trained_at") or meta.get("saved_at")
    trained_text = str(trained)[:19] if trained else "?"
    return (
        info.name,
        classifier,
        accuracy_text,
        trained_text,
        _human_size(info.file_size_bytes),
    )


def _format_table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    """Format a header and rows into a fixed-width, pipe-free table."""
    col_width = [
        max(
            len(str(header[i])),
            max((len(str(row[i])) for row in rows), default=0),
        )
        for i in range(len(header))
    ]
    lines = ["  ".join(str(header[i]).ljust(col_width[i]) for i in range(len(header)))]
    lines.append("  ".join("-" * width for width in col_width))
    lines.extend(
        "  ".join(str(row[i]).ljust(col_width[i]) for i in range(len(header))) for row in rows
    )
    return "\n".join(lines)


def _human_size(num_bytes: int) -> str:
    """Format a byte count as a compact human-readable string."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB"):
        if value < 1024.0 or unit == "MB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} MB"


def _json_safe(value):
    """Convert a value into a JSON-serializable form (FR-213)."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (FR-213)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _plain(value):
    """Convert a numpy scalar to its native Python equivalent for output."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.str_):
        return str(value)
    return value
