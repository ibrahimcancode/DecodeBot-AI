"""Phase 17 — preprocessing & train/test split tests (FR-173-FR-186).

Maps to TC-ML-011..028: scaling correctness, train-only scaler fit (data
leakage regression), LabelEncoder for CSV targets, shuffling, stratification,
reproducibility, and split summary reporting.
"""

import logging

import numpy as np
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from decodebot.ml.dataset import Dataset
from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.preprocessor import (
    PreprocessingError,
    Preprocessor,
    preprocess_and_split,
)

IRIS_FEATURE_NAMES = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
]


@pytest.fixture(scope="module")
def iris():
    return load_dataset("iris", use_cache=False)


def _leaky_dataset() -> Dataset:
    """Synthetic dataset where train/test feature means differ sharply."""
    features = np.zeros((100, 1), dtype=float)
    features[:80, 0] = 0.0
    features[80:, 0] = 100.0
    targets = np.zeros(100, dtype=int)
    targets[50:] = 1
    return Dataset(
        features=features,
        targets=targets,
        feature_names=["f0"],
        source="leaky.csv",
        description="Synthetic leak-check dataset.",
    )


def test_scaled_train_mean_zero_variance_one(iris):
    """FR-173 DoD: post-scaling mean ~ 0 (1e-9), variance ~ 1 (1e-6)."""
    result = preprocess_and_split(iris)
    np.testing.assert_allclose(result.X_train.mean(axis=0), 0.0, atol=1e-9)
    np.testing.assert_allclose(result.X_train.var(axis=0), 1.0, atol=1e-6)
    assert isinstance(result.preprocessor.scaler, StandardScaler)


def test_scaler_fit_on_train_only_leakage_regression():
    """FR-174/FR-184: scaler fit on X_train only; X_test uses train params.

    The last 20% of the synthetic dataset has feature value 100 while the
    first 80% has 0, so a scaler fit on the full data or the test set would
    expose the test distribution through its fitted parameters.
    """
    dataset = _leaky_dataset()
    result = preprocess_and_split(dataset, shuffle=False)

    assert isinstance(result.preprocessor.scaler, StandardScaler)
    np.testing.assert_allclose(result.preprocessor.scaler.mean_, [0.0], atol=1e-9)
    np.testing.assert_allclose(result.preprocessor.scaler.scale_, [1.0], atol=1e-6)
    assert not np.allclose(result.preprocessor.scaler.mean_, [100.0], atol=1.0)

    expected_test = (dataset.features[80:] - 0.0) / 1.0
    np.testing.assert_allclose(result.X_test, expected_test, atol=1e-9)


def test_split_sizes_iris(iris):
    """FR-182 DoD: 150 samples at 0.2 -> 120 train / 30 test."""
    result = preprocess_and_split(iris)
    assert result.X_train.shape == (120, 4)
    assert result.X_test.shape == (30, 4)
    assert result.y_train.shape == (120,)
    assert result.y_test.shape == (30,)
    assert result.split_report.n_train == 120
    assert result.split_report.n_test == 30
    assert result.split_report.summary() == ("Training set: 120 samples | Test set: 30 samples")


def test_stratified_split_class_proportions(iris):
    """FR-183: stratify preserves proportional class representation."""
    result = preprocess_and_split(iris)
    assert result.split_report.stratified is True
    assert result.split_report.train_class_counts == {
        "setosa": 40,
        "versicolor": 40,
        "virginica": 40,
    }
    assert result.split_report.test_class_counts == {
        "setosa": 10,
        "versicolor": 10,
        "virginica": 10,
    }


def test_same_random_state_reproducible(iris):
    """FR-178 DoD: same seed produces bit-identical splits."""
    first = preprocess_and_split(iris, random_state=42)
    second = preprocess_and_split(iris, random_state=42)
    assert np.array_equal(first.X_train, second.X_train)
    assert np.array_equal(first.X_test, second.X_test)
    assert np.array_equal(first.y_train, second.y_train)
    assert np.array_equal(first.y_test, second.y_test)


def test_minmax_scaler_swap(iris):
    """FR-175: scaler_type="minmax" uses MinMaxScaler with [0, 1] output."""
    result = preprocess_and_split(iris, scaler_type="minmax")
    assert isinstance(result.preprocessor.scaler, MinMaxScaler)
    assert result.report.scaler_used == "minmax"
    assert result.X_train.min() >= 0.0
    assert result.X_train.max() <= 1.0


def test_invalid_scaler_type_falls_back_with_warning(iris, caplog):
    """FR-175 edge: unknown scaler_type falls back to StandardScaler + warning."""
    with caplog.at_level(logging.WARNING, logger="decodebot.ml.preprocessor"):
        result = preprocess_and_split(iris, scaler_type="bogus")
    assert isinstance(result.preprocessor.scaler, StandardScaler)
    assert result.report.scaler_used == "standard"
    assert any("falling back to 'standard'" in record.message for record in caplog.records)


def test_none_scaler_leaves_features_unchanged():
    """FR-175: scaler_type="none" returns the raw feature values."""
    dataset = _leaky_dataset()
    result = preprocess_and_split(dataset, shuffle=False, scaler_type="none")
    assert result.preprocessor.scaler is None
    np.testing.assert_allclose(result.X_train, dataset.features[:80])
    np.testing.assert_allclose(result.X_test, dataset.features[80:])


def test_label_encoding_for_csv_string_targets():
    """FR-176: string CSV targets encode to ints with an inverse mapping."""
    features = np.array(
        [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9]],
        dtype=float,
    )
    targets = np.array(["cat", "dog", "cat", "dog", "cat", "dog", "cat", "dog"])
    dataset = Dataset(
        features=features,
        targets=targets,
        feature_names=["a", "b"],
        source="pets.csv",
        description="Synthetic pet dataset.",
    )

    result = preprocess_and_split(dataset)

    assert result.report.encoded_targets is True
    assert result.report.label_mapping == {"cat": 0, "dog": 1}
    assert isinstance(result.preprocessor.label_encoder, LabelEncoder)
    assert np.array_equal(np.unique(result.y_train), [0, 1])
    assert np.array_equal(np.unique(result.y_test), [0, 1])
    assert set(result.split_report.train_class_counts) == {"cat", "dog"}
    assert set(result.split_report.test_class_counts) == {"cat", "dog"}

    decoded = result.preprocessor.inverse_transform_labels(result.y_test)
    assert set(decoded.tolist()).issubset({"cat", "dog"})


def test_stratify_disabled_when_tiny_class(caplog):
    """FR-183 edge: a class with < 2 samples disables stratification safely."""
    features = np.arange(70, dtype=float).reshape(10, 7)
    targets = np.array(["common"] * 9 + ["rare"])
    dataset = Dataset(
        features=features,
        targets=targets,
        feature_names=[f"f{i}" for i in range(7)],
        source="tiny.csv",
        description="Synthetic tiny-class dataset.",
    )

    with caplog.at_level(logging.WARNING, logger="decodebot.ml.preprocessor"):
        result = preprocess_and_split(dataset)

    assert result.split_report.stratified is False
    assert result.X_train.shape[0] + result.X_test.shape[0] == 10
    assert any("fewer than 2 samples" in record.message for record in caplog.records)


def test_shuffle_false_ordered_split(iris, caplog):
    """FR-177 edge: shuffle=False keeps row order (debug/determinism only)."""
    with caplog.at_level(logging.WARNING, logger="decodebot.ml.preprocessor"):
        result = preprocess_and_split(iris, shuffle=False)

    assert result.split_report.shuffled is False
    assert result.split_report.train_class_counts == {
        "setosa": 50,
        "versicolor": 50,
        "virginica": 20,
    }
    assert result.split_report.test_class_counts == {"virginica": 30}
    assert any("shuffle=False" in record.message for record in caplog.records)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_invalid_test_size_rejected(iris, bad):
    """FR-182 edge: test_size outside (0, 1) raises a clear config error."""
    with pytest.raises(PreprocessingError, match="between 0 and 1"):
        preprocess_and_split(iris, test_size=bad)


def test_original_dataset_not_mutated(iris):
    """FR-181: preprocessing never mutates the input dataset."""
    features_before = iris.features.copy()
    targets_before = iris.targets.copy()
    preprocess_and_split(iris)
    np.testing.assert_array_equal(iris.features, features_before)
    np.testing.assert_array_equal(iris.targets, targets_before)


def test_preprocessing_idempotent(iris):
    """FR-181: repeated preprocessing yields identical output."""
    first = preprocess_and_split(iris)
    second = preprocess_and_split(iris)
    np.testing.assert_allclose(first.X_train, second.X_train)
    np.testing.assert_allclose(first.X_test, second.X_test)


def test_preprocessing_report_before_after_ranges(iris):
    """FR-180: report shows pre- and post-scaling feature ranges."""
    result = preprocess_and_split(iris)
    before = result.report.features_before
    after = result.report.features_after

    assert set(before) == set(IRIS_FEATURE_NAMES)
    assert set(after) == set(IRIS_FEATURE_NAMES)

    assert before["petal length (cm)"]["min"] >= 0.9
    assert before["petal length (cm)"]["max"] >= 6.5
    assert abs(after["petal length (cm)"]["max"]) < 3.0


def test_pipeline_composition(iris):
    """FR-179: fitted steps compose into a sklearn Pipeline for raw samples."""
    result = preprocess_and_split(iris)
    pipe = result.preprocessor.pipeline
    assert isinstance(pipe, Pipeline)
    assert "scaler" in dict(pipe.steps)

    raw_sample = np.array([[5.1, 3.5, 1.4, 0.2]])
    scaled_via_pipe = pipe.transform(raw_sample)
    scaled_via_preprocessor = result.preprocessor.transform(raw_sample, None)[0]
    np.testing.assert_allclose(scaled_via_pipe, scaled_via_preprocessor)


def test_pipeline_and_transform_require_fit():
    """Preprocessor guards against use before fitting."""
    preprocessor = Preprocessor()
    with pytest.raises(PreprocessingError, match="before fitting"):
        _ = preprocessor.pipeline
    with pytest.raises(PreprocessingError, match="before transform"):
        preprocessor.transform(np.zeros((1, 2)))


def test_encoded_targets_report_flag_false_for_iris(iris):
    """Iris numeric targets need no LabelEncoder (FR-176)."""
    result = preprocess_and_split(iris)
    assert result.report.encoded_targets is False
    assert result.report.label_mapping is None
    assert result.preprocessor.label_encoder is None
