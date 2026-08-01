"""Phase 18 — model training tests (FR-187-FR-195).

Maps to TC-ML-029..038: KNN baseline workflow, configurable K, K-tuning
elbow scan, multi-classifier swap, training-time tracking, friendly error
handling, and deterministic retraining.
"""

import logging
import time

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import (
    CLASSIFIER_TYPES,
    TrainingError,
    TrainingResult,
    Trainer,
    TuneResult,
    train_pipeline,
)


@pytest.fixture(scope="module")
def iris():
    return load_dataset("iris", use_cache=False)


@pytest.fixture(scope="module")
def iris_split():
    dataset = load_dataset("iris", use_cache=False)
    return preprocess_and_split(dataset, random_state=42)


def test_knn_default_workflow(iris_split):
    """FR-187/FR-188/FR-189: KNN(k=5) fits and predicts through train()."""
    result = Trainer().train(iris_split.X_train, iris_split.y_train)
    assert isinstance(result, TrainingResult)
    assert isinstance(result.model, KNeighborsClassifier)
    assert result.model.get_params()["n_neighbors"] == 5
    assert list(result.model.classes_) == [0, 1, 2]
    prediction = result.model.predict(iris_split.X_train[:1])
    assert prediction.shape == (1,)
    assert prediction[0] in {0, 1, 2}


def test_knn_5_matches_brief_workflow(iris_split):
    """FR-187 AC: the brief's exact INSTANTIATE -> FIT -> PREDICT shape."""
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(iris_split.X_train, iris_split.y_train)
    assert model.predict(iris_split.X_test).shape == (30,)


def test_training_result_fields(iris_split):
    """FR-189/FR-192: result carries model, sizes, and duration."""
    result = Trainer().train(iris_split.X_train, iris_split.y_train)
    assert result.n_samples == 120
    assert result.n_features == 4
    assert result.duration_ms >= 0.0
    assert result.classifier_type == "knn"
    assert result.knn_k == 5
    assert result.random_state == 42
    assert "Model trained in" in result.summary()


def test_configurable_k(iris_split):
    """FR-188: knn_k configures the neighbor count."""
    result = Trainer(knn_k=3).train(iris_split.X_train, iris_split.y_train)
    assert result.model.get_params()["n_neighbors"] == 3
    assert result.knn_k == 3


@pytest.mark.parametrize("bad_k", [0, -5, 2.5, "5"])
def test_invalid_k_rejected(bad_k, iris_split):
    """FR-188 edge: knn_k <= 0 (or non-integer) is a friendly config error."""
    with pytest.raises(TrainingError, match="positive integer"):
        Trainer(knn_k=bad_k)


def test_k_larger_than_training_set(iris_split):
    """FR-187 edge: knn_k > training set size errors before fit()."""
    with pytest.raises(TrainingError, match="larger than the training set"):
        Trainer(knn_k=500).train(iris_split.X_train, iris_split.y_train)


def test_tune_k_returns_scores_and_best(iris_split):
    """FR-190: default 1-20 scan returns (k, error) pairs and best K."""
    result = Trainer().tune_k(
        iris_split.X_train,
        iris_split.y_train,
        iris_split.X_test,
        iris_split.y_test,
    )
    assert isinstance(result, TuneResult)
    assert len(result.scores) == 20
    for k, error in result.scores:
        assert 1 <= k <= 20
        assert 0.0 <= error <= 1.0
    expected_best, _ = min(result.scores, key=lambda pair: (pair[1], pair[0]))
    assert result.best_k == expected_best
    assert result.best_error_rate == min(error for _, error in result.scores)


def test_tune_k_custom_range(iris_split):
    """FR-190: a custom k_range is honored."""
    result = Trainer().tune_k(
        iris_split.X_train,
        iris_split.y_train,
        iris_split.X_test,
        iris_split.y_test,
        k_range=range(1, 6),
    )
    assert [k for k, _ in result.scores] == [1, 2, 3, 4, 5]


def test_tune_k_filters_out_of_range_k(caplog):
    """FR-190: out-of-range K values are skipped with a logged warning."""
    X_train = np.array([[i, i * 2] for i in range(20)], dtype=float)
    y_train = np.array([0] * 10 + [1] * 10)
    X_test = np.array([[0.0, 0.0], [1.0, 2.0]])
    y_test = np.array([0, 1])

    with caplog.at_level(logging.WARNING, logger="decodebot.ml.trainer"):
        result = Trainer().tune_k(X_train, y_train, X_test, y_test, k_range=range(11, 24))

    assert [k for k, _ in result.scores] == list(range(11, 21))
    assert any("out-of-range" in record.message for record in caplog.records)


def test_tune_k_no_valid_k(iris_split):
    """FR-190: a range with no valid K raises a friendly error."""
    with pytest.raises(TrainingError, match="no valid K"):
        Trainer().tune_k(
            iris_split.X_train,
            iris_split.y_train,
            iris_split.X_test,
            iris_split.y_test,
            k_range=range(500, 505),
        )


@pytest.mark.parametrize(
    "classifier_type,expected_class",
    [
        ("knn", KNeighborsClassifier),
        ("decision_tree", DecisionTreeClassifier),
        ("logistic_regression", LogisticRegression),
        ("svm", SVC),
        ("random_forest", RandomForestClassifier),
    ],
)
def test_multi_classifier_swap(classifier_type, expected_class, iris_split):
    """FR-191: every classifier works through the identical train() interface."""
    result = Trainer(classifier_type=classifier_type).train(iris_split.X_train, iris_split.y_train)
    assert isinstance(result.model, expected_class)
    assert result.classifier_type == classifier_type
    predictions = result.model.predict(iris_split.X_test)
    assert predictions.shape == (30,)
    assert set(predictions.tolist()).issubset({0, 1, 2})


def test_classifier_registry_complete():
    """FR-191: the classifier registry exposes all five supported keys."""
    assert set(CLASSIFIER_TYPES) == {
        "knn",
        "decision_tree",
        "logistic_regression",
        "svm",
        "random_forest",
    }


def test_unknown_classifier_falls_back(caplog):
    """FR-191 edge: unknown classifier_type falls back to knn with a warning."""
    with caplog.at_level(logging.WARNING, logger="decodebot.ml.trainer"):
        trainer = Trainer(classifier_type="bogus")
    assert trainer.classifier_type == "knn"
    assert any("falling back to 'knn'" in record.message for record in caplog.records)


def test_mismatched_shapes_friendly_error(iris_split):
    """FR-193: mismatched X/y lengths raise a friendly error, not ValueError."""
    with pytest.raises(TrainingError, match="Row count mismatch"):
        Trainer().train(iris_split.X_train, iris_split.y_train[:10])


def test_non_numeric_features_friendly_error():
    """FR-193: non-numeric features raise a friendly error."""
    X = np.array([["a", "b"], ["c", "d"]])
    y = np.array([0, 1])
    with pytest.raises(TrainingError, match="numeric"):
        Trainer().train(X, y)


def test_single_class_rejected(iris_split):
    """FR-193: a single-class target is rejected before fit."""
    with pytest.raises(TrainingError, match="distinct classes"):
        Trainer().train(iris_split.X_train, np.zeros_like(iris_split.y_train))


def test_reproducible_training_identical_parameters(iris_split):
    """FR-195 DoD: same seed + data yields identical trained parameters."""
    first = Trainer(classifier_type="random_forest", random_state=42).train(
        iris_split.X_train, iris_split.y_train
    )
    second = Trainer(classifier_type="random_forest", random_state=42).train(
        iris_split.X_train, iris_split.y_train
    )

    for est_first, est_second in zip(first.model.estimators_, second.model.estimators_):
        np.testing.assert_array_equal(est_first.tree_.feature, est_second.tree_.feature)
    np.testing.assert_array_equal(
        first.model.predict(iris_split.X_test),
        second.model.predict(iris_split.X_test),
    )


def test_train_pipeline_scaffold(iris):
    """FR-194: the scaffold reports dataset size, split, classifier, timing."""
    report = train_pipeline(iris, random_state=42)

    assert report.dataset_source == "iris"
    assert report.dataset_samples == 150
    assert report.dataset_features == 4
    assert report.n_train == 120
    assert report.n_test == 30
    assert isinstance(report.training_result.model, KNeighborsClassifier)

    summary = report.summary()
    assert "Dataset: iris" in summary
    assert "Training set: 120 samples | Test set: 30 samples" in summary
    assert "Model trained in" in summary
    assert "knn(k=5)" in summary


def test_train_pipeline_custom_config(iris):
    """FR-194/FR-191: custom split ratio and classifier flow through."""
    report = train_pipeline(iris, classifier_type="decision_tree", test_size=0.3, random_state=7)
    assert report.n_train == 105
    assert report.n_test == 45
    assert isinstance(report.training_result.model, DecisionTreeClassifier)
    assert report.training_result.random_state == 7


def test_train_pipeline_runs_under_one_second(iris):
    """FR-194 AC: the full default train run completes within 1 second."""
    start = time.perf_counter()
    train_pipeline(iris, random_state=42)
    assert time.perf_counter() - start < 1.0
