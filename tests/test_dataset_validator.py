"""Phase 16 — dataset validator tests (FR-169-FR-170).

Maps to TC-ML-001..010: missing-value detection, class-count and
sample-count validation, plus the "error"/"drop"/"mean_impute" strategies.
"""

import logging

import numpy as np
import pytest

from decodebot.ml.dataset import Dataset, DatasetValidationError
from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.dataset_validator import validate_dataset


def _make_dataset(features=None, targets=None, feature_names=None):
    return Dataset(
        features=np.asarray(
            features if features is not None else [[5.1, 3.5], [4.9, 3.0], [6.2, 2.2]],
            dtype=np.float64,
        ),
        targets=np.asarray(targets if targets is not None else [0, 1, 2]),
        feature_names=list(feature_names or ["f1", "f2"]),
        target_names=None,
        source="test",
    )


def _balanced_dataset(n_samples, n_classes=2, seed=42):
    rng = np.random.default_rng(seed)
    features = rng.random((n_samples, 2))
    targets = np.arange(n_samples) % n_classes
    return _make_dataset(features=features, targets=targets)


def test_iris_validates_cleanly():
    """FR-169: the Iris benchmark passes validation with a clean report."""
    dataset = load_dataset("iris")
    cleaned, report = validate_dataset(dataset)
    assert report.valid
    assert report.errors == []
    assert report.dropped_rows == 0
    assert cleaned.features.shape == (150, 4)


def test_missing_feature_value_raises_with_column_name():
    """FR-169 AC: missing feature value raises naming the offending column."""
    dataset = _make_dataset(features=[[5.1, 3.5], [np.nan, 3.0], [6.2, 2.2]])
    with pytest.raises(DatasetValidationError, match="f1"):
        validate_dataset(dataset)


def test_missing_target_value_raises():
    """FR-169: missing target value is rejected."""
    dataset = _make_dataset(targets=[0, np.nan, 1])
    with pytest.raises(DatasetValidationError, match="target"):
        validate_dataset(dataset)


def test_single_class_dataset_raises():
    """FR-169 edge: a single-class dataset is rejected."""
    dataset = _make_dataset(targets=[0, 0, 0])
    with pytest.raises(DatasetValidationError, match="2 distinct classes"):
        validate_dataset(dataset)


def test_single_row_dataset_raises():
    """FR-169 edge: a single-row dataset is rejected (it has only 1 class)."""
    dataset = _make_dataset(features=[[5.1, 3.5]], targets=[0])
    with pytest.raises(DatasetValidationError, match="distinct classes"):
        validate_dataset(dataset)


def test_too_few_samples_raises_by_default():
    """FR-169: default minimum sample count is 10."""
    dataset = _balanced_dataset(5)
    with pytest.raises(DatasetValidationError, match="10"):
        validate_dataset(dataset)


def test_min_samples_is_configurable():
    """FR-169: min_samples is configurable."""
    dataset = _balanced_dataset(5)
    cleaned, report = validate_dataset(dataset, min_samples=5)
    assert report.valid
    assert cleaned.features.shape[0] == 5


def test_drop_strategy_removes_missing_rows():
    """FR-170 AC: 'drop' excludes NaN rows and logs the resulting count."""
    rng = np.random.default_rng(0)
    features = rng.random((20, 2))
    targets = np.arange(20) % 2
    features[1, 0] = np.nan
    features[5, 1] = np.nan
    features[9, 0] = np.nan
    dataset = _make_dataset(features=features, targets=targets)
    cleaned, report = validate_dataset(dataset, missing_value_strategy="drop")
    assert report.valid
    assert report.dropped_rows == 3
    assert report.rows_after == 17
    assert cleaned.features.shape == (17, 2)
    assert not np.isnan(cleaned.features).any()


def test_drop_strategy_logs_row_count(caplog):
    """FR-170 AC: the resulting row count is logged."""
    features = np.array([[5.1, 3.5], [np.nan, 3.0], [5.0, 2.0], [np.nan, 2.5]])
    dataset = _make_dataset(features=features, targets=[0, 1, 1, 0])
    with caplog.at_level(logging.WARNING, logger="decodebot.ml.dataset_validator"):
        validate_dataset(dataset, missing_value_strategy="drop", min_samples=1)
    assert any("removed 2 row(s); 2 remain" in record.message for record in caplog.records)


def test_mean_impute_fills_column_mean():
    """FR-170: 'mean_impute' fills numeric NaNs with the column mean."""
    dataset = _make_dataset(
        features=[[5.1, np.nan], [4.9, 3.0], [6.2, 4.0], [5.0, 5.0]],
        targets=[0, 1, 1, 0],
    )
    cleaned, report = validate_dataset(dataset, missing_value_strategy="mean_impute", min_samples=1)
    assert report.valid
    assert report.imputed_columns == ["f2"]
    assert not np.isnan(cleaned.features).any()
    assert cleaned.features[0, 1] == pytest.approx(np.mean([3.0, 4.0, 5.0]))


def test_mean_impute_all_nan_column_falls_back_to_error():
    """FR-170 edge: entirely-NaN column falls back to 'error' with a warning."""
    dataset = _make_dataset(
        features=[[np.nan, 3.5], [np.nan, 3.0], [np.nan, 2.2]],
        targets=[0, 1, 1],
    )
    with pytest.raises(DatasetValidationError, match="entirely-NaN"):
        validate_dataset(dataset, missing_value_strategy="mean_impute")


def test_drop_leaving_single_class_raises():
    """FR-169: drop cannot silently leave a single-class dataset."""
    features = np.array([[5.1, 3.5], [4.9, 3.0], [np.nan, 2.2]])
    dataset = _make_dataset(features=features, targets=[0, 0, 1])
    with pytest.raises(DatasetValidationError, match="2 distinct classes"):
        validate_dataset(dataset, missing_value_strategy="drop", min_samples=1)


def test_unknown_strategy_raises_value_error():
    """FR-170: unknown strategies are rejected up front."""
    dataset = _make_dataset()
    with pytest.raises(ValueError, match="Unknown"):
        validate_dataset(dataset, missing_value_strategy="bogus")
