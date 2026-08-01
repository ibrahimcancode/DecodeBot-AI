"""Phase 19 — prediction tests (FR-196-FR-200).

Maps to TC-ML-039..044: batch prediction on the test set, single-sample
prediction, probability output, the no-trained-model guard, and the
prediction-results table.
"""

import logging

import numpy as np
import pytest
from sklearn.neighbors import KNeighborsClassifier

from decodebot.ml.dataset_loader import load_dataset
from decodebot.ml.predictor import (
    Predictor,
    PredictorError,
    SinglePrediction,
    render_prediction_table,
)
from decodebot.ml.preprocessor import preprocess_and_split
from decodebot.ml.trainer import Trainer

CANONICAL_SETOSA = [5.1, 3.5, 1.4, 0.2]


@pytest.fixture(scope="module")
def iris():
    return load_dataset("iris", use_cache=False)


@pytest.fixture(scope="module")
def iris_predictor(iris):
    split = preprocess_and_split(iris, random_state=42)
    training = Trainer(classifier_type="knn", knn_k=5, random_state=42).train(
        split.X_train, split.y_train
    )
    return split, training.model, iris.target_names


def test_batch_prediction_length_and_valid_labels(iris_predictor):
    """FR-196: batch predict returns correct-length, valid class labels."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    predictions = predictor.predict(model, split.X_test)
    assert len(predictions) == 30
    assert set(predictions) == {"setosa", "versicolor", "virginica"}


def test_batch_prediction_without_mapping_returns_codes(iris_predictor):
    """FR-196 edge: without a label mapping, raw integer codes are returned."""
    split, model, class_names = iris_predictor
    predictions = Predictor().predict(model, split.X_test)
    assert len(predictions) == 30
    assert set(predictions).issubset({0, 1, 2})


def test_single_sample_canonical_setosa(iris_predictor):
    """FR-197 DoD: [5.1, 3.5, 1.4, 0.2] classifies as 'setosa'."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    assert predictor.predict_one(model, CANONICAL_SETOSA) == "setosa"


def test_predict_one_return_proba(iris_predictor):
    """FR-198: probabilities are returned and sum to 1.0 over 3 classes."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    result = predictor.predict_one(model, CANONICAL_SETOSA, return_proba=True)
    assert isinstance(result, SinglePrediction)
    assert result.label == "setosa"
    assert set(result.probabilities) == {"setosa", "versicolor", "virginica"}
    assert sum(result.probabilities.values()) == pytest.approx(1.0)


def test_predict_proba_unsupported_gracefully_omitted(caplog, iris_predictor):
    """FR-198 edge: classifiers without predict_proba log and omit it."""
    split, model, class_names = iris_predictor
    svm = Trainer(classifier_type="svm", random_state=42).train(split.X_train, split.y_train).model
    assert not callable(getattr(svm, "predict_proba", None))

    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    with caplog.at_level(logging.INFO, logger="decodebot.ml.predictor"):
        result = predictor.predict_one(svm, CANONICAL_SETOSA, return_proba=True)

    assert result.label == "setosa"
    assert result.probabilities is None
    assert any("predict_proba" in record.message for record in caplog.records)


def test_predict_without_model_friendly_guard():
    """FR-199: predicting before any model is trained is a friendly error."""
    predictor = Predictor()
    with pytest.raises(PredictorError, match="No trained model found"):
        predictor.predict(None, [[5.1, 3.5, 1.4, 0.2]])
    with pytest.raises(PredictorError, match="No trained model found"):
        predictor.predict_one(None, CANONICAL_SETOSA)


def test_unfitted_model_friendly_guard(iris_predictor):
    """FR-199 edge: an unfitted model never leaks a NotFittedError."""
    split, _, _ = iris_predictor
    unfitted = KNeighborsClassifier(n_neighbors=5)
    predictor = Predictor(preprocessor=split.preprocessor)
    with pytest.raises(PredictorError, match="No trained model found"):
        predictor.predict_one(unfitted, CANONICAL_SETOSA)


def test_wrong_feature_dimension_rejected(iris_predictor):
    """FR-197 edge: wrong-dimension features error before reaching sklearn."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    with pytest.raises(PredictorError, match="Expected 4 feature value"):
        predictor.predict_one(model, [5.1, 3.5, 1.4])


def test_batch_1d_features_rejected(iris_predictor):
    """FR-196 edge: batch features must stay 2-dimensional."""
    split, model, class_names = iris_predictor
    with pytest.raises(PredictorError, match="2-dimensional"):
        Predictor().predict(model, split.X_test[0])


def test_non_numeric_features_rejected(iris_predictor):
    """FR-196/FR-197 edge: non-numeric features raise a friendly error."""
    split, model, class_names = iris_predictor
    with pytest.raises(PredictorError, match="numeric"):
        Predictor().predict(model, [["a", "b", "c", "d"]])


def test_prediction_table_with_true_labels(iris_predictor):
    """FR-200: the table shows index, predicted, true, and correct columns."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    predictions = predictor.predict(model, split.X_test)
    truth = predictor.predict(model, split.X_test)

    text = render_prediction_table(predictions, y_true=truth)
    lines = text.splitlines()
    assert lines[0].startswith("Idx")
    assert "Predicted" in lines[0]
    assert "True" in lines[0]
    assert "Correct?" in lines[0]
    assert len(lines) == 32
    assert any("Yes" in line or "No" in line for line in lines[2:])


def test_prediction_table_without_true_labels(iris_predictor):
    """FR-200 edge: without true labels the table keeps only two columns."""
    split, model, class_names = iris_predictor
    predictions = Predictor().predict(model, split.X_test[:5])
    text = render_prediction_table(predictions)
    assert "Idx" in text.splitlines()[0]
    assert "Predicted" in text.splitlines()[0]
    assert "Correct?" not in text
    assert len(text.splitlines()) == 7


def test_prediction_table_decoded_names(iris_predictor):
    """FR-200: decoded class names appear in the table body."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    text = render_prediction_table(predictor.predict(model, split.X_test[:3]))
    for name in ("setosa", "versicolor", "virginica"):
        assert name in text


def test_predict_one_non_numeric_rejected(iris_predictor):
    """FR-197 edge: non-numeric single-sample features raise a friendly error."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    with pytest.raises(PredictorError, match="numeric"):
        predictor.predict_one(model, ["a", "b", "c", "d"])


def test_predict_one_2d_features_rejected(iris_predictor):
    """FR-197 edge: a nested list of features is rejected for predict_one."""
    split, model, class_names = iris_predictor
    predictor = Predictor(
        class_names=class_names,
        preprocessor=split.preprocessor,
    )
    with pytest.raises(PredictorError, match="1-dimensional"):
        predictor.predict_one(model, [[5.1, 3.5, 1.4, 0.2]])


def test_predict_one_without_preprocessor_uses_raw_values(iris):
    """FR-197 edge: without a preprocessor, raw values classify directly."""
    split = preprocess_and_split(iris, scaler_type="none", random_state=42)
    model = (
        Trainer(classifier_type="knn", knn_k=5, random_state=42)
        .train(split.X_train, split.y_train)
        .model
    )
    predictor = Predictor(class_names=iris.target_names)
    assert predictor.predict_one(model, CANONICAL_SETOSA) == "setosa"


class _FakeModel:
    """Minimal stand-in exposing the sklearn surface Predictor relies on."""

    n_features_in_ = 4

    def __init__(self, predicted, *, proba=None, classes=None):
        self._predicted = predicted
        self._proba = proba
        self.classes_ = classes

    def predict(self, X):
        return self._predicted

    def predict_proba(self, X):
        return self._proba


def test_probabilities_without_class_codes():
    """FR-198 edge: when classes_ is absent, keys are positional indices."""
    model = _FakeModel(np.array([1]), proba=np.array([[0.1, 0.9]]), classes=None)
    result = Predictor(class_names=["setosa", "versicolor"]).predict_one(
        model, CANONICAL_SETOSA, return_proba=True
    )
    assert result.label == "versicolor"
    assert result.probabilities == {"0": 0.1, "1": 0.9}


def test_decode_non_integer_prediction_passes_through():
    """FR-196 edge: string predictions that aren't codes pass through unchanged."""
    model = _FakeModel(np.array(["setosa"]))
    predictions = Predictor(class_names=["setosa", "versicolor"]).predict(model, [[1, 1, 1, 1]])
    assert list(predictions) == ["setosa"]


def test_decode_out_of_range_code_passes_through():
    """FR-196 edge: a code beyond the label table passes through as text."""
    model = _FakeModel(np.array([9]))
    predictions = Predictor(class_names=["setosa", "versicolor", "virginica"]).predict(
        model, [[1, 1, 1, 1]]
    )
    assert list(predictions) == ["9"]


def test_class_name_non_integer_code_passes_through():
    """FR-198 edge: string class codes render as their own label."""
    model = _FakeModel(np.array([0]), proba=np.array([[0.2, 0.8]]), classes=["red", "green"])
    result = Predictor(class_names=["setosa", "versicolor"]).predict_one(
        model, CANONICAL_SETOSA, return_proba=True
    )
    assert result.probabilities == {"red": 0.2, "green": 0.8}


def test_class_name_out_of_range_code_passes_through():
    """FR-198 edge: a class code beyond the label table renders as text."""
    model = _FakeModel(np.array([0]), proba=np.array([[0.2, 0.8]]), classes=[0, 99])
    result = Predictor(class_names=["setosa", "versicolor", "virginica"]).predict_one(
        model, CANONICAL_SETOSA, return_proba=True
    )
    assert result.probabilities == {"setosa": 0.2, "99": 0.8}


def test_plain_converts_numpy_float():
    """FR-200: numpy floating values convert to native floats in output."""
    from decodebot.ml.predictor import _plain

    assert _plain(np.float64(0.5)) == 0.5
    assert _plain(np.str_("setosa")) == "setosa"
    assert _plain(7) == 7
