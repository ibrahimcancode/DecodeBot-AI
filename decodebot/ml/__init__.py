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
from .preprocessor import (
    PreprocessResult,
    PreprocessingError,
    PreprocessingReport,
    Preprocessor,
    SplitReport,
    preprocess_and_split,
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
    "Preprocessor",
    "PreprocessingError",
    "PreprocessingReport",
    "PreprocessResult",
    "SplitReport",
    "preprocess_and_split",
]
