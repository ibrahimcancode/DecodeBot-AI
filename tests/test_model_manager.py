"""Phase 20 — persistence, security, and comparison tests (FR-210-FR-216).

Maps to TC-ML-059..070: the joblib save/reload round-trip, the FR-212
``models/`` loading boundary with explicit opt-in, per-model metadata, the
``models`` listing, the identical-split classifier comparison, and best-model
selection.
"""

import os

import numpy as np
import pytest

from decodebot.ml import model_manager as mm
from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.evaluator import evaluate
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import Trainer

IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]


@pytest.fixture(scope="module")
def iris_split():
    return preprocess_and_split(load_dataset("iris", use_cache=False), random_state=42)


@pytest.fixture(scope="module")
def trained(iris_split):
    return (
        Trainer(classifier_type="knn", knn_k=5, random_state=42)
        .train(iris_split.X_train, iris_split.y_train)
        .model
    )


def _save_and_load_roundtrip(trained, tmp_path):
    """Save ``trained`` into ``tmp_path`` and reload it; return (path, loaded)."""
    path = mm.save_model(
        trained,
        "knn_iris",
        models_dir=str(tmp_path),
        metadata={"classifier_type": "knn"},
    )
    loaded = mm.load_model("knn_iris", models_dir=str(tmp_path))
    return path, loaded


def test_save_creates_joblib_and_metadata_files(trained, tmp_path):
    """FR-210/FR-213: a .joblib plus a companion metadata .json are written."""
    path = mm.save_model(
        trained,
        "knn_iris",
        models_dir=str(tmp_path),
        metadata={"classifier_type": "knn"},
    )
    assert path.endswith("knn_iris.joblib")
    assert os.path.isfile(path)
    assert os.path.isfile(os.path.join(tmp_path, "knn_iris.json"))


def test_save_appends_joblib_extension(trained, tmp_path):
    """FR-210 edge: a bare name gets the .joblib suffix automatically."""
    path = mm.save_model(trained, "bare_name", models_dir=str(tmp_path))
    assert os.path.basename(path) == "bare_name.joblib"


def test_save_requires_predict_capable_model(tmp_path):
    """FR-210 edge: a non-model object is rejected with a friendly error."""
    with pytest.raises(mm.ModelManagerError, match="predict-capable"):
        mm.save_model({"not": "a model"}, "junk", models_dir=str(tmp_path))


def test_save_rejects_empty_and_separator_names(trained, tmp_path):
    """FR-212 edge: empty names and path separators are rejected."""
    with pytest.raises(mm.ModelManagerError, match="empty"):
        mm.save_model(trained, "  ", models_dir=str(tmp_path))
    with pytest.raises(mm.ModelManagerError, match="separators"):
        mm.save_model(trained, "sub/model", models_dir=str(tmp_path))
    with pytest.raises(mm.ModelManagerError, match="separators"):
        mm.save_model(trained, "..\\escape", models_dir=str(tmp_path))


def test_load_reload_identical_predictions(trained, iris_split, tmp_path):
    """FR-211 DoD: a reloaded model predicts identically to the original."""
    _, loaded = _save_and_load_roundtrip(trained, tmp_path)
    original = trained.predict(iris_split.X_test)
    reloaded = loaded.predict(iris_split.X_test)
    np.testing.assert_array_equal(original, reloaded)

    first = evaluate(trained, iris_split.X_test, iris_split.y_test, class_names=IRIS_CLASS_NAMES)
    second = evaluate(loaded, iris_split.X_test, iris_split.y_test, class_names=IRIS_CLASS_NAMES)
    assert first.accuracy == second.accuracy
    assert first.macro_f1 == second.macro_f1


def test_load_missing_model_friendly_error(tmp_path):
    """FR-211 edge: a missing model file errors clearly, not with a crash."""
    with pytest.raises(mm.ModelManagerError, match="file not found"):
        mm.load_model("does_not_exist", models_dir=str(tmp_path))


def test_load_corrupt_file_friendly_error(tmp_path):
    """FR-211 edge: a corrupt .joblib file raises a friendly error."""
    os.makedirs(tmp_path, exist_ok=True)
    with open(os.path.join(tmp_path, "corrupt.joblib"), "wb") as handle:
        handle.write(b"this is not a joblib file")
    with pytest.raises(mm.ModelManagerError, match="corrupted or unreadable"):
        mm.load_model("corrupt", models_dir=str(tmp_path))


def test_load_external_path_blocked_by_default(trained, tmp_path_factory):
    """FR-212 DoD: loading a model from outside models/ is blocked by default."""
    models_dir = str(tmp_path_factory.mktemp("models"))
    outside_dir = str(tmp_path_factory.mktemp("outside"))
    mm.save_model(trained, "ext", models_dir=outside_dir)
    external_path = os.path.join(outside_dir, "ext.joblib")

    with pytest.raises(mm.ModelManagerError, match="blocked by default"):
        mm.load_model(external_path, models_dir=models_dir)


def test_load_external_path_opt_in(trained, iris_split, tmp_path_factory):
    """FR-212 DoD: an explicit opt-in flag permits the external load."""
    models_dir = str(tmp_path_factory.mktemp("models"))
    outside_dir = str(tmp_path_factory.mktemp("outside"))
    mm.save_model(trained, "ext", models_dir=outside_dir)
    external_path = os.path.join(outside_dir, "ext.joblib")

    loaded = mm.load_model(
        external_path,
        models_dir=models_dir,
        allow_external_path=True,
    )
    np.testing.assert_array_equal(
        loaded.predict(iris_split.X_test), trained.predict(iris_split.X_test)
    )


def test_load_bare_filename_resolves_inside_models_dir(trained, tmp_path):
    """FR-212 edge: a bare name with the .joblib suffix stays inside models/."""
    _, loaded = _save_and_load_roundtrip(trained, tmp_path)
    assert callable(getattr(loaded, "predict", None))


def test_list_models_with_metadata(trained, tmp_path):
    """FR-213/FR-214: list_models reports name, size, and metadata."""
    mm.save_model(
        trained,
        "knn_iris",
        models_dir=str(tmp_path),
        metadata={
            "classifier_type": "knn",
            "trained_at": "2026-01-01T00:00:00+00:00",
            "test_accuracy": 0.95,
            "hyperparameters": {"n_neighbors": 5, "metric": "minkowski"},
        },
    )
    infos = mm.list_models(models_dir=str(tmp_path))
    assert len(infos) == 1
    info = infos[0]
    assert info.name == "knn_iris"
    assert info.path.endswith("knn_iris.joblib")
    assert info.file_size_bytes > 0
    assert info.metadata["classifier_type"] == "knn"
    assert info.metadata["test_accuracy"] == 0.95
    assert info.metadata["hyperparameters"]["n_neighbors"] == 5


def test_list_models_empty_dir(tmp_path):
    """FR-214 edge: an empty or missing models dir yields an empty list."""
    assert mm.list_models(models_dir=str(tmp_path)) == []
    assert mm.list_models(models_dir=str(tmp_path / "missing")) == []


def test_render_models_table_empty_message(tmp_path):
    """FR-214 AC: an empty listing renders the friendly empty message."""
    assert mm.render_models_table([]) == mm.NO_SAVED_MODELS_MESSAGE


def test_render_models_table_columns(trained, tmp_path):
    """FR-214: the table shows name, classifier, accuracy, time, and size."""
    mm.save_model(
        trained,
        "knn_iris",
        models_dir=str(tmp_path),
        metadata={
            "classifier_type": "knn",
            "trained_at": "2026-01-01T00:00:00+00:00",
            "test_accuracy": 0.95,
        },
    )
    table = mm.render_models_table(mm.list_models(models_dir=str(tmp_path)))
    for token in ("Model", "Classifier", "Test Acc", "Trained", "Size", "knn_iris"):
        assert token in table


def test_compare_models_identical_split(iris_split):
    """FR-215 DoD: every classifier trains/evaluates on the identical split."""
    report = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    assert isinstance(report, mm.ComparisonReport)
    assert report.n_test == 30
    assert [r.classifier_type for r in report.results] == [
        "knn",
        "decision_tree",
        "logistic_regression",
    ]

    for result in report.results:
        predictions = result.model.predict(iris_split.X_test)
        accuracy = float(np.mean(predictions == iris_split.y_test))
        assert accuracy == pytest.approx(result.accuracy, abs=1e-9)
        assert 0.0 <= result.f1 <= 1.0
        assert result.duration_ms > 0.0


def test_compare_models_is_deterministic(iris_split):
    """FR-208/FR-215: repeated comparisons on the same split are identical."""
    first = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    second = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    for a, b in zip(first.results, second.results):
        assert a.accuracy == b.accuracy
        assert a.precision == b.precision
        assert a.recall == b.recall
        assert a.f1 == b.f1


def test_comparison_best_is_max_f1(iris_split):
    """FR-216: report.best() picks the highest macro-F1 classifier."""
    report = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    best = report.best()
    assert best.f1 == max(r.f1 for r in report.results)
    assert callable(getattr(report.best_model(), "predict", None))
    assert report.best_model() is best.model


def test_render_comparison_table_marks_best(iris_split):
    """FR-215/FR-216: the table lists all classifiers and stars the best."""
    report = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    table = mm.render_comparison_table(report)
    for name in ("Classifier", "Accuracy", "Precision", "Recall", "F1"):
        assert name in table
    assert f"* {report.best().classifier_type}" in table


def test_save_best_model_records_metadata(iris_split, tmp_path):
    """FR-216: save_best_model persists only the top-F1 model with metadata."""
    report = mm.compare_models(iris_split, class_names=IRIS_CLASS_NAMES)
    best_type = report.best().classifier_type
    best_f1 = report.best().f1

    path = mm.save_best_model(report, models_dir=str(tmp_path))
    assert os.path.basename(path) == "best_model.joblib"

    infos = mm.list_models(models_dir=str(tmp_path))
    assert len(infos) == 1
    assert infos[0].metadata["classifier_type"] == best_type
    assert infos[0].metadata["macro_f1"] == best_f1
    assert infos[0].metadata["test_accuracy"] == report.best().accuracy
