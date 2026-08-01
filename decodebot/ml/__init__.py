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
- ``save_model()`` / ``load_model()`` / ``list_models()`` — model
  persistence and the ``models`` listing (FR-210-FR-214) with ``ModelInfo``,
  ``ModelManagerError``, and ``render_models_table()``.
- ``compare_models()`` / ``save_best_model()`` — same-split classifier
  comparison and best-model selection (FR-215-FR-216) with
  ``ComparisonReport``, ``ClassifierComparison``, and
  ``render_comparison_table()``.
- ``confusion_matrix_heatmap()`` / ``k_tuning_elbow()`` /
  ``scaling_comparison()`` / ``model_comparison_bar()`` — file-based
  visualization saved to ``outputs/`` (FR-217-FR-221) with
  ``VisualizationError`` and ``VisualizationUnavailableError``.
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
from .model_manager import (
    ClassifierComparison,
    ComparisonReport,
    ModelInfo,
    ModelManagerError,
    compare_models,
    list_models,
    load_model,
    render_comparison_table,
    render_models_table,
    save_best_model,
    save_model,
)
from .visualization import (
    DEFAULT_OUTPUTS_DIR,
    VisualizationError,
    VisualizationUnavailableError,
    confusion_matrix_heatmap,
    k_tuning_elbow,
    matplotlib_available,
    model_comparison_bar,
    scaling_comparison,
)
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
    "ClassifierComparison",
    "ComparisonReport",
    "ModelInfo",
    "ModelManagerError",
    "compare_models",
    "list_models",
    "load_model",
    "render_comparison_table",
    "render_models_table",
    "save_best_model",
    "save_model",
    "DEFAULT_OUTPUTS_DIR",
    "VisualizationError",
    "VisualizationUnavailableError",
    "confusion_matrix_heatmap",
    "k_tuning_elbow",
    "matplotlib_available",
    "model_comparison_bar",
    "scaling_comparison",
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
