"""Week 2 Compliance Matrix gate — the 8 mandatory DecodeLabs rows.

Rows 1-5 (dataset loading, preprocessing scaling, shuffle/split, KNN
workflow, model training) are implemented in Phases 16-18 and must pass.
Rows 6-7 (prediction, evaluation beyond accuracy) land in Phase 19. Row 8
(the full automated suite + gate) lands in Phase 21 with the ML command
wiring and must pass as part of the combined suite.
"""

import logging

import numpy as np
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


def test_row_8_testing(tmp_path):
    """Row 8: full test suite covers every pipeline stage; gate passes.

    End-to-end through the registered ML commands: classification, dispatch,
    the full train -> evaluate -> predict -> persist -> reload flow, plus the
    config keys, help grouping, and lazy startup. This test participates in
    the suite that the gate runs, so its green status is itself the gate.
    """
    from decodebot.core.dispatcher import dispatch
    from decodebot.core.intents import Intent
    from decodebot.core.session import SessionState
    from decodebot.core.rule_engine import classify_intent
    from decodebot.rules.help_about_version import get_help_text
    from decodebot.ml import app_ml

    session = SessionState()
    session.config = {
        "ml_dataset": "iris",
        "ml_target_column": None,
        "ml_test_size": 0.2,
        "ml_random_state": 42,
        "knn_k": 5,
        "classifier_type": "knn",
        "scaler_type": "standard",
        "ml_missing_value_strategy": "error",
        "models_dir": str(tmp_path),
        "ml_outputs_dir": str(tmp_path),
        "ml_log_level": "INFO",
    }

    for cmd, intent in (
        ("train", Intent.TRAIN),
        ("predict", Intent.PREDICT),
        ("evaluate", Intent.EVALUATE),
        ("explore", Intent.EXPLORE),
        ("models", Intent.MODELS),
        ("compare", Intent.COMPARE),
        ("tune-k", Intent.TUNE_K),
    ):
        assert classify_intent(cmd, session) == intent

    assert "Machine Learning:" in get_help_text()

    explore_text = dispatch(Intent.EXPLORE, session)
    assert "Dataset: iris" in explore_text

    train_text = dispatch(Intent.TRAIN, session)
    assert "Saved model to" in train_text
    assert "Test accuracy:" in train_text

    session.last_input = "predict 5.1,3.5,1.4,0.2"
    predict_text = dispatch(Intent.PREDICT, session)
    assert "setosa" in predict_text

    evaluate_text = dispatch(Intent.EVALUATE, session)
    assert "Confusion Matrix" in evaluate_text

    models_text = dispatch(Intent.MODELS, session)
    assert "Model" in models_text

    compare_text = dispatch(Intent.COMPARE, session)
    assert "Classifier" in compare_text

    tune_text = dispatch(Intent.TUNE_K, session)
    assert "Best K:" in tune_text

    saved = app_ml.list_models(models_dir=str(tmp_path))
    assert saved, "train must persist a model"
    reloaded = app_ml.load_model(saved[0].name, models_dir=str(tmp_path))
    assert callable(getattr(reloaded, "predict", None))
