"""DecodeBot AI — Machine Learning Engine package (Week 2).

All ``scikit-learn`` / ``pandas`` / ``numpy`` / ``matplotlib`` / ``joblib``
usage is confined to this package (FR-229, NFR-072). The Chatbot Engine
never imports this package at startup, preserving its fast launch time
(FR-232).

Public API:
- ``Dataset`` and the dataset exception hierarchy (FR-164).
- ``load_dataset()`` — Iris or CSV loading (FR-164-FR-166, FR-168).
- ``render_explore_report()`` — dataset understanding report (FR-172).
- ``validate_dataset()`` — integrity validation (FR-169-FR-170).
- ``preprocess_and_split()`` — scaling, encoding, and stratified splitting
  (FR-173-FR-186) with ``Preprocessor``, ``PreprocessResult``,
  ``PreprocessingReport``, ``SplitReport``, and ``PreprocessingError``.
- ``Trainer`` / ``train_pipeline()`` — model training (FR-187-FR-195) with
  ``TrainingResult``, ``TuneResult``, ``TrainRunReport``, and
  ``TrainingError``.
- ``Predictor`` / ``render_prediction_table()`` — batch and single-sample
  prediction (FR-196-FR-200) with ``SinglePrediction`` and
  ``PredictorError``.
- ``evaluate()`` / ``cross_validate()`` / ``dummy_baseline()`` — model
  evaluation (FR-201-FR-209) with ``EvaluationReport``,
  ``CrossValidationResult``, and ``EvaluationError``.
"""

from .dataset import (
    Dataset,
    DatasetError,
    DatasetLoadError,
    DatasetValidationError,
    FeatureFrame,
    FeatureMatrix,
    TargetVector,
)
from .dataset_loader import load_dataset, render_explore_report
from .dataset_validator import ValidationReport, validate_dataset
from .evaluator import (
    CrossValidationResult,
    EvaluationError,
    EvaluationReport,
    cross_validate,
    dummy_baseline,
    evaluate,
)
from .predictor import (
    Predictor,
    PredictorError,
    SinglePrediction,
    render_prediction_table,
)
from .preprocessor import (
    PreprocessResult,
    PreprocessingError,
    PreprocessingReport,
    Preprocessor,
    SplitReport,
    preprocess_and_split,
)
from .trainer import (
    TrainRunReport,
    TrainingError,
    TrainingResult,
    Trainer,
    TuneResult,
    train_pipeline,
)

__all__ = [
    "Dataset",
    "DatasetError",
    "DatasetLoadError",
    "DatasetValidationError",
    "FeatureFrame",
    "FeatureMatrix",
    "TargetVector",
    "load_dataset",
    "render_explore_report",
    "ValidationReport",
    "validate_dataset",
    "Predictor",
    "PredictorError",
    "SinglePrediction",
    "render_prediction_table",
    "CrossValidationResult",
    "EvaluationError",
    "EvaluationReport",
    "cross_validate",
    "dummy_baseline",
    "evaluate",
    "Preprocessor",
    "PreprocessingError",
    "PreprocessingReport",
    "PreprocessResult",
    "SplitReport",
    "preprocess_and_split",
    "Trainer",
    "TrainingError",
    "TrainingResult",
    "TuneResult",
    "TrainRunReport",
    "train_pipeline",
]
