"""Phase 19 — evaluation tests (FR-201-FR-209).

Maps to TC-ML-045..058: accuracy, confusion matrix, per-class and macro
precision/recall/F1, the "accuracy mirage" warning, the EvaluationReport
object, cross-validation, determinism, and the dummy baseline.
"""

import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier

from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.evaluator import (
    CrossValidationResult,
    EvaluationError,
    EvaluationReport,
    cross_validate,
    dummy_baseline,
    evaluate,
)
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import Trainer

IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]


@pytest.fixture(scope="module")
def iris():
    return load_dataset("iris", use_cache=False)


@pytest.fixture(scope="module")
def iris_trained():
    dataset = load_dataset("iris", use_cache=False)
    split = preprocess_and_split(dataset, random_state=42)
    model = (
        Trainer(classifier_type="knn", knn_k=5, random_state=42)
        .train(split.X_train, split.y_train)
        .model
    )
    return split, model


def test_accuracy_reported(iris_trained):
    """FR-201: overall accuracy is reported and ≥ 0.85 on Iris."""
    split, model = iris_trained
    report = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    assert isinstance(report, EvaluationReport)
    assert report.accuracy >= 0.85
    assert report.accuracy <= 1.0


def test_confusion_matrix_shape_and_total(iris_trained):
    """FR-202: a 3x3 confusion matrix whose cells sum to the test size."""
    split, model = iris_trained
    report = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    assert report.confusion_matrix.shape == (3, 3)
    assert int(report.confusion_matrix.sum()) == 30
    diagonal = int(np.trace(report.confusion_matrix))
    off_diagonal = int(report.confusion_matrix.sum() - np.trace(report.confusion_matrix))
    assert diagonal + off_diagonal == 30


def test_per_class_and_macro_metrics(iris_trained):
    """FR-203: precision/recall/F1 per class plus macro averages."""
    split, model = iris_trained
    report = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    for name in IRIS_CLASS_NAMES:
        assert name in report.precision
        assert name in report.recall
        assert name in report.f1
        assert 0.0 <= report.precision[name] <= 1.0
        assert 0.0 <= report.recall[name] <= 1.0
        assert 0.0 <= report.f1[name] <= 1.0
    assert 0.0 <= report.macro_precision <= 1.0
    assert 0.0 <= report.macro_recall <= 1.0
    assert 0.0 <= report.macro_f1 <= 1.0


def test_class_names_length_mismatch_rejected(iris_trained):
    """FR-203 edge: misaligned class_names raise a friendly error."""
    split, model = iris_trained
    with pytest.raises(EvaluationError, match="must match"):
        evaluate(model, split.X_test, split.y_test, class_names=["setosa"])


def test_zero_predicted_class_is_well_defined():
    """FR-203 edge: zero-predicted classes yield 0.0, not a warning/crash."""
    X = np.array([[i, i * 2] for i in range(22)], dtype=float)
    y = np.array([0] * 20 + [1] * 2)
    model = DummyClassifier(strategy="most_frequent")
    model.fit(X, y)

    report = evaluate(model, X, y, class_names=["major", "minor"])
    assert report.f1["minor"] == 0.0
    assert report.precision["minor"] == 0.0
    assert report.recall["minor"] == 0.0


def test_accuracy_mirage_warning_on_imbalanced_data():
    """FR-204 DoD: a synthetic imbalanced set triggers the warning."""
    rng = np.random.RandomState(7)
    X = rng.rand(104, 4)
    y = np.array(["majority"] * 100 + ["minority_a"] * 2 + ["minority_b"] * 2)
    model = DummyClassifier(strategy="most_frequent")
    model.fit(X, y)

    report = evaluate(model, X, y)
    assert report.accuracy > 0.95
    assert report.accuracy_mirage_warning is not None
    assert "accuracy alone may be misleading" in report.accuracy_mirage_warning
    assert "minority" in report.accuracy_mirage_warning


def test_no_mirage_warning_on_balanced_iris(iris_trained):
    """FR-204 DoD: the balanced Iris dataset does not trigger the warning."""
    split, model = iris_trained
    report = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    assert report.accuracy_mirage_warning is None


def test_evaluation_is_deterministic(iris_trained):
    """FR-208: repeated evaluate calls yield bit-identical values."""
    split, model = iris_trained
    first = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    second = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES)
    assert first.accuracy == second.accuracy
    assert first.macro_f1 == second.macro_f1
    assert first.precision == second.precision
    assert first.recall == second.recall
    assert first.f1 == second.f1
    np.testing.assert_array_equal(first.confusion_matrix, second.confusion_matrix)


def test_dummy_baseline_accuracy(iris_trained):
    """FR-209: the most-frequent baseline is reported alongside accuracy."""
    split, model = iris_trained
    baseline = dummy_baseline(split.X_train, split.y_train, split.X_test, split.y_test)
    assert isinstance(baseline, float)
    assert 0.0 <= baseline <= 1.0

    report = evaluate(
        model,
        split.X_test,
        split.y_test,
        class_names=IRIS_CLASS_NAMES,
        baseline_accuracy=baseline,
    )
    assert report.baseline_accuracy == baseline
    assert "Baseline (most-frequent)" in report.render()


def test_cross_validate_five_fold(iris):
    """FR-207: 5-fold CV reports mean ± std across five folds."""
    result = cross_validate(
        KNeighborsClassifier(n_neighbors=5),
        iris.features,
        iris.targets,
        cv=5,
        random_state=42,
    )
    assert isinstance(result, CrossValidationResult)
    assert len(result.scores) == 5
    assert 0.0 <= result.mean <= 1.0
    assert result.std >= 0.0
    assert "5-fold CV accuracy" in result.summary()


def test_cross_validate_cv_too_large_rejected():
    """FR-207 edge: cv > smallest class count errors clearly."""
    X = np.arange(12).reshape(6, 2).astype(float)
    y = np.array([0, 0, 0, 1, 1, 1])
    with pytest.raises(EvaluationError, match="exceeds the smallest class"):
        cross_validate(KNeighborsClassifier(n_neighbors=3), X, y, cv=4)


def test_render_never_accuracy_alone(iris_trained):
    """FR-206/NFR-080: the render always includes the deeper metrics."""
    split, model = iris_trained
    text = evaluate(model, split.X_test, split.y_test, class_names=IRIS_CLASS_NAMES).render()
    assert "Accuracy" in text
    assert "Confusion Matrix" in text
    assert "Macro average" in text
    assert "Per-class metrics" in text


def test_evaluate_without_model_friendly_guard(iris_trained):
    """FR-199/FR-206 edge: evaluating before training is a friendly error."""
    split, _ = iris_trained
    with pytest.raises(EvaluationError, match="No trained model found"):
        evaluate(None, split.X_test, split.y_test)


def test_evaluate_row_count_mismatch(iris_trained):
    """FR-205 edge: mismatched X/y rows raise a friendly error."""
    split, model = iris_trained
    with pytest.raises(EvaluationError, match="Row count mismatch"):
        evaluate(model, split.X_test, split.y_test[:10])
