"""Phase 16 — dataset loader tests (FR-164-FR-168, FR-171-FR-172).

Maps to TC-ML-001..010: shape, features, classes, balance, CSV path
support, caching, and metadata for the Iris benchmark dataset.
"""

import os

import pytest

from decodebot.ml import dataset_loader
from decodebot.ml.dataset import Dataset, DatasetLoadError, DatasetValidationError
from decodebot.ml.dataset_loader import load_dataset, render_explore_report

IRIS_FEATURE_NAMES = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
]
IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]

WELL_FORMED_CSV = [
    "sepal_length,sepal_width,petal_length,petal_width,species",
    "5.1,3.5,1.4,0.2,setosa",
    "4.9,3.0,1.4,0.2,setosa",
    "6.2,2.9,4.3,1.3,versicolor",
    "5.9,3.2,4.5,1.5,versicolor",
    "6.7,3.0,5.6,2.1,virginica",
    "6.4,3.2,5.3,2.3,virginica",
]

NON_NUMERIC_FEATURE_CSV = [
    "color,length,species",
    "red,5.1,setosa",
    "blue,4.9,setosa",
    "green,6.2,versicolor",
]


@pytest.fixture(autouse=True)
def _clear_cache():
    """Isolate the in-memory dataset cache between tests (FR-168)."""
    dataset_loader._CACHE.clear()
    yield
    dataset_loader._CACHE.clear()


def _write_csv(tmp_path, lines):
    path = tmp_path / "data.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_load_iris_default_returns_normalized_dataset():
    """FR-164: load_dataset("iris") returns a normalized Dataset."""
    dataset = load_dataset()
    assert isinstance(dataset, Dataset)
    assert dataset.features.shape == (150, 4)
    assert dataset.targets.shape == (150,)
    assert dataset.feature_names == IRIS_FEATURE_NAMES
    assert dataset.target_names == IRIS_CLASS_NAMES
    assert dataset.features.dtype.kind == "f"


def test_load_iris_benchmark_metrics():
    """FR-164 AC: 150 samples, 4 features, 3 classes."""
    dataset = load_dataset("iris")
    assert dataset.describe()["samples"] == 150
    assert dataset.describe()["features"] == 4
    assert dataset.describe()["classes"] == 3


def test_describe_reports_class_counts():
    """FR-166 AC: describe() reports exact Iris class counts."""
    dataset = load_dataset("iris")
    meta = dataset.describe()
    assert meta["class_counts"] == {
        "setosa": 50,
        "versicolor": 50,
        "virginica": 50,
    }


def test_class_balance_iris_is_perfectly_balanced():
    """FR-167 AC: Iris balance ratio reports as 1.0."""
    dataset = load_dataset("iris")
    assert dataset.class_balance() == 1.0
    assert dataset.describe()["balance_ratio"] == 1.0


def test_load_csv_well_formed(tmp_path):
    """FR-165 AC: load_dataset(path, target_column=...) works for a good CSV."""
    path = _write_csv(tmp_path, WELL_FORMED_CSV)
    dataset = load_dataset(path, target_column="species")
    assert dataset.features.shape == (6, 4)
    assert dataset.targets.shape == (6,)
    assert dataset.feature_names == [
        "sepal_length",
        "sepal_width",
        "petal_length",
        "petal_width",
    ]
    assert dataset.target_names == ["setosa", "versicolor", "virginica"]
    assert dataset.describe()["classes"] == 3
    assert dataset.source == os.path.abspath(path)


def test_load_csv_requires_target_column_argument(tmp_path):
    """FR-165 edge: CSV without target_column raises DatasetValidationError."""
    path = _write_csv(tmp_path, WELL_FORMED_CSV)
    with pytest.raises(DatasetValidationError, match="target column"):
        load_dataset(path)


def test_load_csv_missing_target_column_name(tmp_path):
    """FR-165 edge: unknown target column name raises DatasetValidationError."""
    path = _write_csv(tmp_path, WELL_FORMED_CSV)
    with pytest.raises(DatasetValidationError, match="'nope'"):
        load_dataset(path, target_column="nope")


def test_load_csv_rejects_non_numeric_feature_column(tmp_path):
    """FR-165 edge: non-numeric feature columns are rejected."""
    path = _write_csv(tmp_path, NON_NUMERIC_FEATURE_CSV)
    with pytest.raises(DatasetValidationError, match="Non-numeric feature column"):
        load_dataset(path, target_column="species")


def test_load_nonexistent_csv_is_friendly_error():
    """FR-171 AC: a missing CSV path raises a friendly DatasetLoadError."""
    with pytest.raises(DatasetLoadError, match="check the path"):
        load_dataset("definitely_missing.csv", target_column="species")


def test_second_call_returns_cached_object_without_reload(monkeypatch):
    """FR-168 AC: a second call returns the cached object, no re-load."""
    original = dataset_loader._load_iris
    calls = {"n": 0}

    def _counting_load():
        calls["n"] += 1
        return original()

    monkeypatch.setattr(dataset_loader, "_load_iris", _counting_load)
    first = load_dataset("iris")
    second = load_dataset("iris")
    assert first is second
    assert calls["n"] == 1


def test_use_cache_false_bypasses_cache(monkeypatch):
    """FR-168 edge: use_cache=False forces a fresh load."""
    original = dataset_loader._load_iris
    calls = {"n": 0}

    def _counting_load():
        calls["n"] += 1
        return original()

    monkeypatch.setattr(dataset_loader, "_load_iris", _counting_load)
    load_dataset("iris")
    load_dataset("iris", use_cache=False)
    assert calls["n"] == 2


def test_explore_report_contains_dataset_metadata():
    """FR-172 AC data side: report shows samples, classes, balance, stats."""
    dataset = load_dataset("iris")
    report = render_explore_report(dataset)
    assert "Samples: 150" in report
    assert "setosa" in report
    assert "virginica" in report
    assert "balance" in report
    assert "min / max / mean / std" in report
