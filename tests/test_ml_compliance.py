"""Week 2 Compliance Matrix gate — the 8 mandatory DecodeLabs rows.

Rows 1-5 (dataset loading, preprocessing scaling, shuffle/split, KNN
workflow, model training) are implemented in Phases 16-18 and must pass.
Rows 6-7 (prediction, evaluation beyond accuracy) land in Phase 19. Row 8
maps to later phases (full suite + gate) and is marked skipped until its
pipeline stage lands.
"""

import logging

import numpy as np
import pytest
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from decodebot.ml.dataset_loader import load_dataset, render_explore_report
from decodebot.ml.dataset_validator import validate_dataset
from decodebot.ml.evaluator import evaluate
from decodebot.ml.predictor import Predictor
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import Trainer


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


def test_row_2_preprocessing_scaling():
    """Row 2: scaling applied; post-scaling mean ~ 0 and variance ~ 1.

    Maps to FR-173-FR-181 / TC-ML-011..020.
    """
    dataset = load_dataset("iris", use_cache=False)
    result = preprocess_and_split(dataset, random_state=42)

    assert isinstance(result.preprocessor.scaler, StandardScaler)
    np.testing.assert_allclose(result.X_train.mean(axis=0), 0.0, atol=1e-9)
    np.testing.assert_allclose(result.X_train.var(axis=0), 1.0, atol=1e-6)
    assert result.split_report.n_train == 120
    assert result.split_report.n_test == 30


def test_row_3_shuffle_and_split():
    """Row 3: shuffled, stratified 80/20 split with configurable seed.

    Maps to FR-182-FR-186 / TC-ML-021..028.
    """
    dataset = load_dataset("iris", use_cache=False)
    result = preprocess_and_split(dataset, random_state=42)

    assert result.split_report.shuffled is True
    assert result.split_report.stratified is True
    assert result.split_report.n_train == 120
    assert result.split_report.n_test == 30
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

    again = preprocess_and_split(dataset, random_state=42)
    assert np.array_equal(result.X_train, again.X_train)
    assert np.array_equal(result.X_test, again.X_test)
    assert np.array_equal(result.y_train, again.y_train)
    assert np.array_equal(result.y_test, again.y_test)


def test_row_4_knn_classification():
    """Row 4: KNeighborsClassifier follows the official workflow.

    Maps to FR-187-FR-189 / TC-ML-029..034.
    """
    dataset = load_dataset("iris", use_cache=False)
    split = preprocess_and_split(dataset, random_state=42)
    result = Trainer(classifier_type="knn", knn_k=5, random_state=42).train(
        split.X_train, split.y_train
    )

    assert isinstance(result.model, KNeighborsClassifier)
    assert result.model.get_params()["n_neighbors"] == 5
    assert list(result.model.classes_) == [0, 1, 2]
    predictions = result.model.predict(split.X_test)
    assert predictions.shape == (30,)
    assert set(predictions.tolist()).issubset({0, 1, 2})


def test_row_5_train_model():
    """Row 5: training completes and the model is retrievable.

    Maps to FR-189, FR-191, FR-195 / TC-ML-035..038.
    """
    dataset = load_dataset("iris", use_cache=False)
    split = preprocess_and_split(dataset, random_state=42)
    result = Trainer(classifier_type="knn", knn_k=5, random_state=42).train(
        split.X_train, split.y_train
    )

    assert result.model.predict(split.X_train[:1]).shape == (1,)
    assert result.duration_ms >= 0.0

    swapped = Trainer(classifier_type="decision_tree", random_state=42).train(
        split.X_train, split.y_train
    )
    assert isinstance(swapped.model, DecisionTreeClassifier)


def test_row_6_predictions_on_test_set():
    """Row 6: batch + single-sample prediction (FR-196-FR-200).

    Maps to TC-ML-039..044 / Phase 19 DoD.
    """
    dataset = load_dataset("iris", use_cache=False)
    split = preprocess_and_split(dataset, random_state=42)
    training = Trainer(classifier_type="knn", knn_k=5, random_state=42).train(
        split.X_train, split.y_train
    )

    predictor = Predictor(
        class_names=dataset.target_names,
        preprocessor=split.preprocessor,
    )
    predictions = predictor.predict(training.model, split.X_test)
    assert len(predictions) == 30
    assert set(predictions) == {"setosa", "versicolor", "virginica"}

    assert predictor.predict_one(training.model, [5.1, 3.5, 1.4, 0.2]) == "setosa"


def test_row_7_evaluate_beyond_accuracy():
    """Row 7: confusion matrix, precision, recall, F1 (FR-201-FR-209).

    Maps to TC-ML-045..058 / Phase 19 DoD — never accuracy alone (NFR-080).
    """
    dataset = load_dataset("iris", use_cache=False)
    split = preprocess_and_split(dataset, random_state=42)
    training = Trainer(classifier_type="knn", knn_k=5, random_state=42).train(
        split.X_train, split.y_train
    )

    report = evaluate(
        training.model,
        split.X_test,
        split.y_test,
        class_names=dataset.target_names,
    )
    assert report.accuracy >= 0.85
    assert report.confusion_matrix.shape == (3, 3)
    assert int(report.confusion_matrix.sum()) == 30
    assert set(report.precision) == {"setosa", "versicolor", "virginica"}
    assert set(report.recall) == {"setosa", "versicolor", "virginica"}
    assert set(report.f1) == {"setosa", "versicolor", "virginica"}
    assert 0.0 <= report.macro_f1 <= 1.0
    assert report.accuracy_mirage_warning is None

    text = report.render()
    assert "Accuracy" in text
    assert "Confusion Matrix" in text
    assert "Macro average" in text


@pytest.mark.skip(reason="Phase 22: full automated ML suite + gate — all of Category R")
def test_row_8_testing():
    """Row 8: full test suite covers every pipeline stage; gate passes."""
