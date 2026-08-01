"""File-based visualization for the ML Engine (FR-217-FR-221).

Renders evaluation and preprocessing results as PNG plots saved to a
configurable ``outputs/`` directory: the confusion-matrix heatmap (FR-217),
the K-tuning elbow curve (FR-218), the before/after scaling comparison
(FR-219), and the model-comparison bar chart (FR-220). Rendering is
non-blocking and file-based via the matplotlib ``Agg`` backend, which works in
headless environments (FR-221).

matplotlib is imported lazily: when it is not installed, every function raises
the friendly ``VisualizationUnavailableError`` instead of failing at import
time, keeping ``decodebot.ml`` importable everywhere (FR-229, FR-232).
"""

import logging
import os

from .dataset import DatasetError

logger = logging.getLogger(__name__)

DEFAULT_OUTPUTS_DIR = "outputs/"
UNAVAILABLE_MESSAGE = (
    "matplotlib is not installed, so plots cannot be rendered. Install it "
    "with 'pip install matplotlib' to enable visualization (FR-217-FR-221)."
)

_PYPLOT = None


class VisualizationError(DatasetError):
    """Raised for invalid visualization input or a failed render (FR-217-FR-221)."""


class VisualizationUnavailableError(VisualizationError):
    """Raised when matplotlib is not installed (FR-221 graceful degradation)."""


def matplotlib_available() -> bool:
    """Return True when matplotlib can be imported (FR-221)."""
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        return False
    return True


def _pyplot():
    """Import matplotlib.pyplot lazily behind the Agg backend (FR-221)."""
    global _PYPLOT
    if _PYPLOT is None:
        try:
            import matplotlib
        except ImportError:
            raise VisualizationUnavailableError(UNAVAILABLE_MESSAGE) from None
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        _PYPLOT = plt
    return _PYPLOT


def confusion_matrix_heatmap(
    report,
    *,
    path: str | None = None,
    outputs_dir: str = DEFAULT_OUTPUTS_DIR,
) -> str:
    """Save the evaluation's confusion matrix as a heatmap PNG (FR-217).

    Args:
        report: An ``EvaluationReport`` from ``evaluate()``.
        path: Explicit output path; defaults to ``outputs_dir/confusion_matrix.png``.
        outputs_dir: Directory for saved plots (default ``"outputs/"``).

    Returns:
        The absolute path of the saved PNG file.

    Raises:
        VisualizationUnavailableError: When matplotlib is not installed.
        VisualizationError: For malformed report input.
    """
    matrix = getattr(report, "confusion_matrix", None)
    class_names = getattr(report, "class_names", None)
    if matrix is None or class_names is None:
        raise VisualizationError(
            "confusion_matrix_heatmap requires an EvaluationReport from " "evaluate() (FR-217)."
        )
    plt = _pyplot()

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(matrix, cmap="Blues", interpolation="nearest")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            ax.text(
                col,
                row,
                str(int(matrix[row, col])),
                ha="center",
                va="center",
                color="white" if int(matrix[row, col]) > matrix.max() / 2 else "black",
            )
    return _save(plt, fig, "confusion_matrix.png", path, outputs_dir)


def k_tuning_elbow(
    tune_result,
    *,
    path: str | None = None,
    outputs_dir: str = DEFAULT_OUTPUTS_DIR,
) -> str:
    """Save the K-tuning elbow curve as a PNG (FR-218).

    Args:
        tune_result: A ``TuneResult`` from ``Trainer.tune_k()``.
        path: Explicit output path; defaults to ``outputs_dir/k_tuning_elbow.png``.
        outputs_dir: Directory for saved plots (default ``"outputs/"``).

    Returns:
        The absolute path of the saved PNG file.

    Raises:
        VisualizationUnavailableError: When matplotlib is not installed.
        VisualizationError: For malformed input.
    """
    scores = getattr(tune_result, "scores", None)
    best_k = getattr(tune_result, "best_k", None)
    if not scores or best_k is None:
        raise VisualizationError(
            "k_tuning_elbow requires a TuneResult from Trainer.tune_k() (FR-218)."
        )
    plt = _pyplot()

    k_values = [int(k) for k, _ in scores]
    errors = [float(error) for _, error in scores]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(k_values, errors, marker="o", linestyle="-", color="#1f77b4")
    ax.axvline(best_k, color="#d62728", linestyle="--", label=f"Best K={best_k}")
    ax.set_xlabel("K (neighbors)")
    ax.set_ylabel("Error rate")
    ax.set_title("K-Neighbors Tuning — Elbow Curve")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(plt, fig, "k_tuning_elbow.png", path, outputs_dir)


def scaling_comparison(
    preprocess_result,
    *,
    path: str | None = None,
    outputs_dir: str = DEFAULT_OUTPUTS_DIR,
) -> str:
    """Save the before/after feature-range comparison as a PNG (FR-219).

    For every feature, plots its min/max range before and after scaling,
    making the FR-180 scaling effect visible.

    Args:
        preprocess_result: A ``PreprocessResult`` from ``preprocess_and_split()``.
        path: Explicit output path; defaults to ``outputs_dir/scaling_before_after.png``.
        outputs_dir: Directory for saved plots (default ``"outputs/"``).

    Returns:
        The absolute path of the saved PNG file.

    Raises:
        VisualizationUnavailableError: When matplotlib is not installed.
        VisualizationError: For malformed input.
    """
    report = getattr(preprocess_result, "report", None)
    if report is None or not getattr(report, "features_before", None):
        raise VisualizationError(
            "scaling_comparison requires a PreprocessResult from "
            "preprocess_and_split() (FR-219)."
        )
    plt = _pyplot()

    names = list(report.features_before.keys())
    before_min = [float(report.features_before[name]["min"]) for name in names]
    before_max = [float(report.features_before[name]["max"]) for name in names]
    after = report.features_after
    after_min = [float(after[name]["min"]) for name in names]
    after_max = [float(after[name]["max"]) for name in names]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    x = range(len(names))
    for axis, (lo, hi, title) in zip(
        axes,
        ((before_min, before_max, "Before Scaling"), (after_min, after_max, "After Scaling")),
    ):
        axis.bar(x, [hi_i - lo_i for hi_i, lo_i in zip(hi, lo)], bottom=lo, color="#4c72b0")
        axis.set_xticks(x)
        axis.set_xticklabels(names, rotation=45, ha="right")
        axis.set_title(title)
        axis.grid(True, axis="y", alpha=0.3)
    fig.suptitle(f"Feature Ranges — Scaler: {report.scaler_used}")
    return _save(plt, fig, "scaling_before_after.png", path, outputs_dir)


def model_comparison_bar(
    report,
    *,
    path: str | None = None,
    outputs_dir: str = DEFAULT_OUTPUTS_DIR,
) -> str:
    """Save the model-comparison bar chart as a PNG (FR-220).

    Plots test accuracy and macro-F1 for every classifier in a
    ``ComparisonReport`` from ``compare_models()``.

    Args:
        report: A ``ComparisonReport`` from ``compare_models()``.
        path: Explicit output path; defaults to ``outputs_dir/model_comparison.png``.
        outputs_dir: Directory for saved plots (default ``"outputs/"``).

    Returns:
        The absolute path of the saved PNG file.

    Raises:
        VisualizationUnavailableError: When matplotlib is not installed.
        VisualizationError: For malformed input.
    """
    results = getattr(report, "results", None)
    if not results:
        raise VisualizationError(
            "model_comparison_bar requires a ComparisonReport from " "compare_models() (FR-220)."
        )
    plt = _pyplot()

    names = [str(result.classifier_type) for result in results]
    accuracies = [float(result.accuracy) for result in results]
    f1_scores = [float(result.f1) for result in results]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(names))
    width = 0.35
    ax.bar([i - width / 2 for i in x], accuracies, width, label="Accuracy", color="#4c72b0")
    ax.bar([i + width / 2 for i in x], f1_scores, width, label="Macro-F1", color="#dd8452")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Classifier Comparison on Identical Split")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    return _save(plt, fig, "model_comparison.png", path, outputs_dir)


def _save(plt, fig, filename: str, path: str | None, outputs_dir: str) -> str:
    """Save a figure to disk and close it (FR-221 non-blocking)."""
    if path is None:
        path = os.path.join(outputs_dir, filename)
    if not os.path.splitext(path)[1]:
        path += ".png"
    absolute = os.path.abspath(path)
    os.makedirs(os.path.dirname(absolute) or ".", exist_ok=True)
    try:
        fig.savefig(absolute, dpi=150, bbox_inches="tight")
    except Exception as exc:
        logger.error("Failed to save plot to %s.", absolute)
        raise VisualizationError(
            f"Couldn't save the plot to '{absolute}'. Check the path and try again."
        ) from exc
    finally:
        plt.close(fig)
    logger.info("Saved plot to %s.", absolute)
    return absolute
