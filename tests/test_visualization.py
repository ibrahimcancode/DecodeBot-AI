"""Phase 20 — visualization tests (FR-217-FR-221).

The four render functions write PNG plots to ``outputs/`` via the non-blocking
matplotlib ``Agg`` backend (FR-221), which works headless. When matplotlib is
not installed — as in the current environment — the functions must instead
raise the friendly ``VisualizationUnavailableError`` instead of crashing;
those degradation paths are asserted unconditionally, while the real plotting
tests skip.
"""

import os

import pytest

from decodebot.ml import model_manager as mm
from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.evaluator import evaluate
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import Trainer
from decodebot.ml.visualization import (
    VisualizationError,
    VisualizationUnavailableError,
    confusion_matrix_heatmap,
    k_tuning_elbow,
    matplotlib_available,
    model_comparison_bar,
    scaling_comparison,
)

IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]
HAVE_MATPLOTLIB = matplotlib_available()
REQUIRES_MATPLOTLIB = pytest.mark.skipif(
    not HAVE_MATPLOTLIB, reason="matplotlib is not installed in this environment"
)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture(scope="module")
def iris_split():
    return preprocess_and_split(load_dataset("iris", use_cache=False), random_state=42)


@pytest.fixture(scope="module")
def evaluation_report(iris_split):
    model = (
        Trainer(classifier_type="knn", knn_k=5, random_state=42)
        .train(iris_split.X_train, iris_split.y_train)
        .model
    )
    return evaluate(model, iris_split.X_test, iris_split.y_test, class_names=IRIS_CLASS_NAMES)


@pytest.fixture(scope="module")
def tune_result(iris_split):
    return Trainer(knn_k=5, random_state=42).tune_k(
        iris_split.X_train,
        iris_split.y_train,
        iris_split.X_test,
        iris_split.y_test,
    )


@pytest.fixture(scope="module")
def comparison_report(iris_split):
    return mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)


def _assert_valid_png(path):
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 100
    with open(path, "rb") as handle:
        assert handle.read(8) == PNG_MAGIC


@REQUIRES_MATPLOTLIB
def test_confusion_matrix_heatmap_saves_png(evaluation_report, tmp_path):
    """FR-217: the heatmap renders to a valid PNG under outputs/."""
    path = confusion_matrix_heatmap(evaluation_report, path=str(tmp_path / "cm.png"))
    _assert_valid_png(path)
    assert path == str(tmp_path / "cm.png")


@REQUIRES_MATPLOTLIB
def test_k_tuning_elbow_saves_png(tune_result, tmp_path):
    """FR-218: the elbow curve renders to a valid PNG."""
    path = k_tuning_elbow(tune_result, outputs_dir=str(tmp_path))
    _assert_valid_png(path)


@REQUIRES_MATPLOTLIB
def test_scaling_comparison_saves_png(iris_split, tmp_path):
    """FR-219: the before/after scaling plot renders to a valid PNG."""
    path = scaling_comparison(iris_split, outputs_dir=str(tmp_path))
    _assert_valid_png(path)


@REQUIRES_MATPLOTLIB
def test_model_comparison_bar_saves_png(comparison_report, tmp_path):
    """FR-220: the comparison bar chart renders to a valid PNG."""
    path = model_comparison_bar(comparison_report, outputs_dir=str(tmp_path))
    _assert_valid_png(path)


@REQUIRES_MATPLOTLIB
def test_renders_with_agg_backend_in_headless(tmp_path):
    """FR-221: rendering uses the headless Agg backend (no display needed)."""
    import matplotlib

    split = preprocess_and_split(load_dataset("iris", use_cache=False), random_state=42)
    tune = Trainer(knn_k=5, random_state=42).tune_k(
        split.X_train, split.y_train, split.X_test, split.y_test
    )
    k_tuning_elbow(tune, outputs_dir=str(tmp_path))
    assert matplotlib.get_backend() == "Agg"


@pytest.mark.skipif(HAVE_MATPLOTLIB, reason="matplotlib is installed")
def test_unavailable_matplotlib_raises_friendly_error(iris_split):
    """FR-221: without matplotlib, rendering degrades to a friendly error."""
    tune = Trainer(knn_k=5, random_state=42).tune_k(
        iris_split.X_train,
        iris_split.y_train,
        iris_split.X_test,
        iris_split.y_test,
    )
    with pytest.raises(VisualizationUnavailableError, match="matplotlib is not installed"):
        k_tuning_elbow(tune)


@pytest.mark.skipif(HAVE_MATPLOTLIB, reason="matplotlib is installed")
def test_matplotlib_available_flag_matches_environment():
    """FR-221: the availability flag is consistent with the environment."""
    assert matplotlib_available() is False


def test_heatmap_rejects_malformed_input():
    """FR-217 edge: a non-EvaluationReport input errors clearly."""
    with pytest.raises(VisualizationError, match="EvaluationReport"):
        confusion_matrix_heatmap(None)


def test_elbow_rejects_malformed_input():
    """FR-218 edge: a non-TuneResult input errors clearly."""
    with pytest.raises(VisualizationError, match="TuneResult"):
        k_tuning_elbow(None)


def test_scaling_rejects_malformed_input():
    """FR-219 edge: a non-PreprocessResult input errors clearly."""
    with pytest.raises(VisualizationError, match="PreprocessResult"):
        scaling_comparison(None)


def test_comparison_rejects_malformed_input():
    """FR-220 edge: a non-ComparisonReport input errors clearly."""
    with pytest.raises(VisualizationError, match="ComparisonReport"):
        model_comparison_bar(None)
