"""Week 2 Compliance Matrix gate — the 8 mandatory DecodeLabs rows.

Row 1 (dataset loading & understanding) is implemented in Phase 16 and must
pass. Rows 2-8 map to later phases (FR-173+) and are marked skipped until
their pipeline stages land.
"""

import logging

import pytest

from decodebot.ml.dataset_loader import load_dataset, render_explore_report
from decodebot.ml.dataset_validator import validate_dataset


def test_row_1_load_and_understand_dataset(caplog):
    """Row 1: Iris loads; shape, names, classes, balance inspectable & logged.

    Maps to FR-164-FR-172 / TC-ML-001..010.
    """
    with caplog.at_level(logging.INFO, logger="decodebot.ml.dataset_loader"):
        dataset = load_dataset("iris", use_cache=False)

    assert dataset.features.shape == (150, 4)
    assert dataset.targets.shape == (150,)
    assert dataset.feature_names == [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    assert dataset.target_names == ["setosa", "versicolor", "virginica"]

    meta = dataset.describe()
    assert meta["samples"] == 150
    assert meta["features"] == 4
    assert meta["classes"] == 3
    assert meta["class_counts"] == {"setosa": 50, "versicolor": 50, "virginica": 50}
    assert meta["balance_ratio"] == 1.0

    cleaned, report = validate_dataset(dataset)
    assert report.valid
    assert cleaned.features.shape == (150, 4)

    report_text = render_explore_report(dataset)
    assert "Samples: 150" in report_text
    assert "setosa" in report_text
    assert "balance" in report_text

    assert any("Dataset loaded" in record.message for record in caplog.records)


@pytest.mark.skip(reason="Phase 17: StandardScaler scaling — FR-173-FR-181")
def test_row_2_preprocessing_scaling():
    """Row 2: scaling applied; post-scaling mean ~ 0 and variance ~ 1."""


@pytest.mark.skip(reason="Phase 17: shuffle + train/test split — FR-182-FR-186")
def test_row_3_shuffle_and_split():
    """Row 3: shuffled, stratified 80/20 split with configurable seed."""


@pytest.mark.skip(reason="Phase 18: KNN INSTANTIATE -> FIT -> PREDICT — FR-187-FR-195")
def test_row_4_knn_classification():
    """Row 4: KNeighborsClassifier follows the official workflow."""


@pytest.mark.skip(reason="Phase 18: model.fit(X_train, y_train) — FR-189, FR-191")
def test_row_5_train_model():
    """Row 5: training completes and the model is retrievable."""


@pytest.mark.skip(reason="Phase 19: predictions on the test set — FR-196-FR-200")
def test_row_6_predictions_on_test_set():
    """Row 6: model.predict(X_test) returns valid-length class labels."""


@pytest.mark.skip(reason="Phase 19: evaluation beyond accuracy — FR-201-FR-209")
def test_row_7_evaluate_beyond_accuracy():
    """Row 7: confusion matrix, precision, recall, F1 computed and reported."""


@pytest.mark.skip(reason="Phase 22: full automated ML suite + gate — all of Category R")
def test_row_8_testing():
    """Row 8: full test suite covers every pipeline stage; gate passes."""
