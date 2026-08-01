"""Model evaluation for the ML Engine (FR-201-FR-209).

Computes accuracy alongside the deeper diagnostic metrics mandated by the
Week 2 brief — confusion matrix, per-class and macro precision/recall/F1 —
assembles them into a single ``EvaluationReport`` consumed identically by the
CLI, GUI, and visualization layers, surfaces the "accuracy mirage" warning on
imbalanced data, supports cross-validation and a dummy-baseline comparison,
and guarantees deterministic, repeatable metric values.

Reference: Week 2 brief — "Evaluation" and "accuracy is a lie".
"""

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.exceptions import NotFittedError

from .dataset import DatasetError

logger = logging.getLogger(__name__)

NO_MODEL_MESSAGE = "No trained model found — run 'train' first."


class EvaluationError(DatasetError):
    """Raised for invalid evaluation input or a missing trained model (FR-205, FR-207)."""


@dataclass
class CrossValidationResult:
    """Outcome of a cross-validation run (FR-207).

    Attributes:
        cv: Number of folds used.
        scores: Per-fold accuracy scores, length ``cv``.
        mean: Mean fold accuracy.
        std: Standard deviation of fold accuracies.
    """

    cv: int
    scores: list[float]
    mean: float
    std: float

    def summary(self) -> str:
        """Return the one-line mean ± std summary (FR-207 acceptance)."""
        return f"{self.cv}-fold CV accuracy: {self.mean:.3f} ± {self.std:.3f}"


@dataclass
class EvaluationReport:
    """Complete evaluation output for one model/test-set pair (FR-205).

    Attributes:
        accuracy: Overall accuracy via ``sklearn.metrics.accuracy_score``
            (FR-201).
        confusion_matrix: Square array of shape (n_classes, n_classes),
            rows = actual, columns = predicted (FR-202).
        class_names: Class labels aligned to the confusion matrix axis.
        precision: Per-class precision, keyed by class name (FR-203).
        recall: Per-class recall, keyed by class name (FR-203).
        f1: Per-class F1 score, keyed by class name (FR-203).
        macro_precision: Macro-averaged precision (FR-203).
        macro_recall: Macro-averaged recall (FR-203).
        macro_f1: Macro-averaged F1 (FR-203).
        accuracy_mirage_warning: The FR-204 educational warning, or None when
            the data is balanced or accuracy is not misleading.
        baseline_accuracy: Most-frequent-class baseline accuracy (FR-209),
            or None when not requested.
        n_test: Number of evaluated test samples.
    """

    accuracy: float
    confusion_matrix: np.ndarray
    class_names: list[str]
    precision: dict[str, float]
    recall: dict[str, float]
    f1: dict[str, float]
    macro_precision: float
    macro_recall: float
    macro_f1: float
    accuracy_mirage_warning: str | None
    baseline_accuracy: float | None
    n_test: int

    def render(self) -> str:
        """Render the report in a readable, boxed CLI-style format (FR-206).

        Accuracy is always reported alongside the confusion matrix and
        per-class precision/recall/F1 — never alone (NFR-080).
        """
        lines: list[str] = []
        lines.append("=" * 40)
        lines.append(" Evaluation Report")
        lines.append("-" * 40)
        lines.append(f" Accuracy: {self.accuracy:.4f}")
        if self.baseline_accuracy is not None:
            lines.append(f" Baseline (most-frequent): {self.baseline_accuracy:.4f}")
        if self.accuracy_mirage_warning:
            lines.append(f" {self.accuracy_mirage_warning}")
        lines.append("-" * 40)
        lines.append(" Confusion Matrix (rows = actual, cols = predicted)")
        lines.extend(_render_matrix(self.confusion_matrix, self.class_names))
        lines.append("-" * 40)
        lines.append(" Per-class metrics (precision / recall / F1)")
        for name in self.class_names:
            lines.append(
                f"  {name:<12s} {self.precision[name]:.3f} / "
                f"{self.recall[name]:.3f} / {self.f1[name]:.3f}"
            )
        lines.append("-" * 40)
        lines.append(
            f" Macro average: precision {self.macro_precision:.3f} | "
            f"recall {self.macro_recall:.3f} | F1 {self.macro_f1:.3f}"
        )
        lines.append(f" Samples evaluated: {self.n_test}")
        lines.append("=" * 40)
        return "\n".join(lines)


def evaluate(
    model,
    X_test,
    y_test,
    *,
    class_names: list[str] | None = None,
    baseline_accuracy: float | None = None,
    imbalance_ratio: float = 2.0,
    mirage_accuracy_threshold: float = 0.95,
    mirage_recall_gap: float = 0.15,
) -> EvaluationReport:
    """Evaluate a trained model on a test set (FR-201-FR-206, FR-208).

    Args:
        model: A fitted scikit-learn classifier, or None (FR-199/FR-206 edge).
        X_test: Preprocessed test features of shape (n_test, n_features).
        y_test: True test targets aligned with ``X_test``.
        class_names: Human-readable class names aligned to the model's class
            order. Defaults to the model's ``classes_`` rendered as strings.
        baseline_accuracy: Optional most-frequent baseline accuracy from
            ``dummy_baseline`` (FR-209), included in the report when set.
        imbalance_ratio: Min/max class-count ratio above which the data is
            considered imbalanced (FR-167, FR-204).
        mirage_accuracy_threshold: Accuracy above which the mirage warning may
            trigger (FR-204).
        mirage_recall_gap: How much lower a minority class's recall must be
            than accuracy to trigger the warning (FR-204).

    Returns:
        One ``EvaluationReport`` consumed identically by the CLI, GUI, and
        visualization layers (FR-205).

    Raises:
        EvaluationError: For a missing/unfitted model or malformed input.

    Note:
        Metric computation is deterministic: calling ``evaluate`` twice on the
        same model/test-set pair yields bit-identical values (FR-208).
    """
    if model is None:
        raise EvaluationError(NO_MODEL_MESSAGE)
    X = _coerce_features(X_test)
    y = np.asarray(y_test)
    _validate_shapes(X, y)

    try:
        predictions = np.asarray(model.predict(X))
    except NotFittedError as exc:
        raise EvaluationError(NO_MODEL_MESSAGE) from exc
    if len(predictions) != len(y):
        raise EvaluationError(
            f"Prediction count mismatch: model returned {len(predictions)} "
            f"predictions for {len(y)} test samples."
        )

    labels = _class_labels(model, y)
    names = _resolve_class_names(class_names, labels)

    accuracy = float(accuracy_score(y, predictions))
    matrix = confusion_matrix(y, predictions, labels=labels)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, predictions, labels=labels, zero_division=0
    )

    report = EvaluationReport(
        accuracy=accuracy,
        confusion_matrix=matrix,
        class_names=names,
        precision=_paired(names, precision),
        recall=_paired(names, recall),
        f1=_paired(names, f1),
        macro_precision=_plain(float(precision.mean())),
        macro_recall=_plain(float(recall.mean())),
        macro_f1=_plain(float(f1.mean())),
        accuracy_mirage_warning=_mirage_warning(
            y,
            names,
            recall,
            accuracy,
            imbalance_ratio=imbalance_ratio,
            mirage_accuracy_threshold=mirage_accuracy_threshold,
            mirage_recall_gap=mirage_recall_gap,
        ),
        baseline_accuracy=_plain(baseline_accuracy) if baseline_accuracy is not None else None,
        n_test=int(y.shape[0]),
    )

    logger.info(
        "Evaluated model on %d samples: accuracy=%.4f, macro-F1=%.4f.",
        report.n_test,
        report.accuracy,
        report.macro_f1,
    )
    return report


def dummy_baseline(X_train, y_train, X_test, y_test) -> float:
    """Return the most-frequent-class baseline accuracy (FR-209).

    Trains a ``DummyClassifier(strategy="most_frequent")`` on the training
    set and scores it on the test set, making the trained model's improvement
    over a naive baseline explicit.

    Args:
        X_train: Training features.
        y_train: Training targets.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        The baseline accuracy in ``[0.0, 1.0]``.
    """
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(np.asarray(X_train), np.asarray(y_train))
    return _plain(float(accuracy_score(np.asarray(y_test), baseline.predict(np.asarray(X_test)))))


def cross_validate(
    estimator,
    X,
    y,
    *,
    cv: int = 5,
    random_state: int = 42,
    scoring: str = "accuracy",
) -> CrossValidationResult:
    """Cross-validate an estimator with stratified k-fold (FR-207).

    Args:
        estimator: A scikit-learn estimator (cloned and refitted per fold).
        X: Full feature matrix.
        y: Full target labels.
        cv: Number of folds (default 5).
        random_state: Seed for reproducible fold shuffling (FR-208).
        scoring: Scorer name passed to ``cross_val_score``.

    Returns:
        A ``CrossValidationResult`` with per-fold scores and mean ± std.

    Raises:
        EvaluationError: If ``cv`` exceeds the smallest class's sample count,
            since stratified folds require at least one sample per class per
            fold (FR-207 edge).
    """
    X = _coerce_features(X)
    y = np.asarray(y)
    _validate_shapes(X, y)

    _, counts = np.unique(y, return_counts=True)
    smallest = int(counts.min()) if counts.size else 0
    if cv > smallest:
        raise EvaluationError(
            f"cv={cv} exceeds the smallest class sample count ({smallest}); "
            "stratified cross-validation needs at least one sample per class "
            "per fold. Reduce cv or add more data."
        )

    kfold = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    scores = cross_val_score(estimator, X, y, cv=kfold, scoring=scoring)
    logger.info(
        "%d-fold CV on %d samples: %.3f ± %.3f.",
        cv,
        X.shape[0],
        float(scores.mean()),
        float(scores.std()),
    )
    return CrossValidationResult(
        cv=int(cv),
        scores=[_plain(float(score)) for score in scores],
        mean=_plain(float(scores.mean())),
        std=_plain(float(scores.std())),
    )


def _coerce_features(X) -> np.ndarray:
    """Return X as a float64 2-D ndarray or raise a friendly error."""
    try:
        arr = np.asarray(X, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise EvaluationError("Features must be numeric.") from exc
    if arr.ndim != 2:
        raise EvaluationError(
            f"Features must be 2-dimensional (samples x features); got {arr.ndim}D."
        )
    return arr


def _validate_shapes(X: np.ndarray, y: np.ndarray) -> None:
    """Validate feature dimensionality and row-count agreement (FR-205)."""
    if X.shape[0] != y.shape[0]:
        raise EvaluationError(
            f"Row count mismatch: X has {X.shape[0]} rows but y has {y.shape[0]}."
        )


def _class_labels(model, y) -> list:
    """Return the stable, sorted class labels used for metric alignment."""
    classes = getattr(model, "classes_", None)
    if classes is not None and len(classes) > 0:
        return list(classes)
    return sorted(set(np.asarray(y).tolist()))


def _resolve_class_names(class_names: list[str] | None, labels: list) -> list[str]:
    """Resolve display names aligned to the class label order (FR-203)."""
    if class_names is None:
        return [str(label) for label in labels]
    if len(class_names) != len(labels):
        raise EvaluationError(
            f"class_names has {len(class_names)} entries but the model has "
            f"{len(labels)} classes; they must match."
        )
    return list(class_names)


def _paired(names: list[str], values) -> dict[str, float]:
    """Zip class names with metric values into a dict."""
    return {name: _plain(float(value)) for name, value in zip(names, values)}


def _mirage_warning(
    y,
    names: list[str],
    recall,
    accuracy: float,
    *,
    imbalance_ratio: float,
    mirage_accuracy_threshold: float,
    mirage_recall_gap: float,
) -> str | None:
    """Build the FR-204 "accuracy mirage" warning, or None (FR-204)."""
    _, counts = np.unique(np.asarray(y), return_counts=True)
    present = [int(count) for count in counts]
    if not present:
        return None
    balance = max(present) / min(present)
    if balance < imbalance_ratio:
        return None
    if accuracy < mirage_accuracy_threshold:
        return None

    minority = int(np.argmin(counts))
    recall_by_index = {int(i): float(value) for i, value in enumerate(recall)}
    if recall_by_index.get(minority, 1.0) > accuracy - mirage_recall_gap:
        return None

    name = names[minority] if minority < len(names) else str(minority)
    return (
        f"⚠️ High accuracy but lower recall on '{name}' — " "accuracy alone may be misleading here."
    )


def _render_matrix(matrix: np.ndarray, names: list[str]) -> list[str]:
    """Render the confusion matrix as aligned text rows."""
    label_width = max((len(name) for name in names), default=4)
    rows = [" " * (label_width + 2) + " ".join(str(i) for i in range(matrix.shape[1]))]
    for row_index, name in enumerate(names):
        cells = " ".join(str(int(value)) for value in matrix[row_index])
        rows.append(f"{name:<{label_width}}  {cells}")
    return rows


def _plain(value):
    """Convert a numpy scalar to its native Python equivalent for output."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.str_):
        return str(value)
    return value
