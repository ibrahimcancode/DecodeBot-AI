"""Dataset integrity validation (FR-169-FR-170).

Validates any loaded dataset for missing values, consistent feature
dimensionality, a minimum of two distinct classes, and a minimum sample
count. Supports three missing-value strategies: ``"error"`` (default,
reject), ``"drop"`` (drop affected rows), and ``"mean_impute"`` (fill
numeric NaNs with the column mean).

Reference: Week 2 brief — data quality discipline before any training step.
"""

import logging
from dataclasses import dataclass, field

import numpy as np

from .dataset import Dataset, DatasetValidationError

logger = logging.getLogger(__name__)

MISSING_VALUE_STRATEGIES: tuple[str, ...] = ("error", "drop", "mean_impute")
DEFAULT_MIN_SAMPLES: int = 10
_EMPTY_TOKENS: frozenset[str] = frozenset({"", "nan", "na", "null", "none"})


@dataclass
class ValidationReport:
    """Summary of a single dataset validation pass (FR-169).

    Attributes:
        valid: Whether the dataset passed every check.
        errors: Human-readable validation failures.
        warnings: Non-fatal notes surfaced during handling.
        rows_after: Sample count of the returned dataset.
        dropped_rows: Rows removed by the ``"drop"`` strategy.
        imputed_columns: Feature columns filled by ``"mean_impute"``.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows_after: int = 0
    dropped_rows: int = 0
    imputed_columns: list[str] = field(default_factory=list)


def validate_dataset(
    dataset: Dataset,
    *,
    missing_value_strategy: str = "error",
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> tuple[Dataset, ValidationReport]:
    """Validate a dataset and apply the configured missing-value strategy.

    Checks (FR-169):
    - No missing/NaN values in features or targets.
    - Consistent 2-D feature dimensionality matching the target row count.
    - At least two distinct classes.
    - A minimum sample count sufficient for a train/test split.

    Args:
        dataset: The dataset to validate.
        missing_value_strategy: One of ``"error"`` (reject on missing values,
            default), ``"drop"`` (drop affected rows and log the resulting
            count), or ``"mean_impute"`` (fill numeric NaNs with the column
            mean). ``"mean_impute"`` on an entirely-NaN column falls back to
            ``"error"`` for that column with a logged warning (FR-170).
        min_samples: Minimum sample count (default 10).

    Returns:
        A ``(cleaned_dataset, report)`` tuple. The cleaned dataset equals the
        input unless ``drop``/``mean_impute`` transformed it.

    Raises:
        DatasetValidationError: When validation fails under the active
            strategy, with a clear, actionable message.
        ValueError: When ``missing_value_strategy`` is unknown.

    Reference: Week 2 brief — data quality discipline.
    """
    if missing_value_strategy not in MISSING_VALUE_STRATEGIES:
        raise ValueError(
            f"Unknown missing_value_strategy {missing_value_strategy!r}; "
            f"expected one of {', '.join(MISSING_VALUE_STRATEGIES)}."
        )

    report = ValidationReport(rows_after=int(dataset.features.shape[0]))
    features = np.asarray(dataset.features)
    targets = np.asarray(dataset.targets)

    if features.ndim != 2:
        _fail(
            report,
            f"Feature matrix must be 2-dimensional (samples x features); " f"got {features.ndim}D.",
        )
    elif features.shape[0] != targets.shape[0]:
        _fail(
            report,
            f"Row count mismatch: features have {features.shape[0]} rows but "
            f"targets have {targets.shape[0]} rows.",
        )

    cleaned = dataset
    if report.valid:
        feature_nan_cols = _nan_columns(features, dataset.feature_names)
        target_has_nan = any(_is_missing(value) for value in targets)

        if feature_nan_cols or target_has_nan:
            if missing_value_strategy == "error":
                _fail(report, _missing_value_message(feature_nan_cols, target_has_nan))
            elif missing_value_strategy == "drop":
                cleaned = _drop_missing_rows(dataset, target_has_nan)
                report.dropped_rows = int(dataset.features.shape[0] - cleaned.features.shape[0])
                report.rows_after = int(cleaned.features.shape[0])
                logger.warning(
                    "Missing-value strategy 'drop': removed %d row(s); %d remain.",
                    report.dropped_rows,
                    report.rows_after,
                )
            else:  # mean_impute
                if target_has_nan:
                    _fail(
                        report,
                        "Target column contains missing values; 'mean_impute' "
                        "only applies to numeric feature columns.",
                    )
                else:
                    cleaned, report.imputed_columns, failed_cols = _mean_impute(dataset)
                    if failed_cols:
                        logger.warning(
                            "Cannot mean-impute entirely-NaN column(s): %s — "
                            "falling back to 'error'.",
                            ", ".join(failed_cols),
                        )
                        _fail(
                            report,
                            "Cannot mean-impute entirely-NaN feature column(s): "
                            + ", ".join(failed_cols)
                            + ".",
                        )
                    if report.imputed_columns:
                        logger.info(
                            "Missing-value strategy 'mean_impute': filled " "column(s) %s.",
                            ", ".join(report.imputed_columns),
                        )

    if report.valid:
        n_samples = int(cleaned.features.shape[0])
        unique_classes = np.unique(cleaned.targets)
        if len(unique_classes) < 2:
            _fail(
                report,
                "Dataset must contain at least 2 distinct classes; "
                f"found only {len(unique_classes)}.",
            )
        elif n_samples < min_samples:
            _fail(
                report,
                f"Dataset has {n_samples} sample(s); at least {min_samples} are "
                "required for a train/test split.",
            )
        else:
            report.rows_after = n_samples

    if report.errors:
        logger.error("Dataset validation failed: %s", "; ".join(report.errors))
        raise DatasetValidationError("; ".join(report.errors))

    logger.info(
        "Dataset validation passed: %d samples, %d classes.",
        int(cleaned.features.shape[0]),
        len(np.unique(cleaned.targets)),
    )
    return cleaned, report


def _fail(report: ValidationReport, message: str) -> None:
    """Record a validation failure on the report (FR-169)."""
    report.errors.append(message)
    report.valid = False


def _nan_columns(features: np.ndarray, feature_names: list[str]) -> list[str]:
    """Return the names of feature columns containing any missing value."""
    if features.ndim != 2:
        return []
    columns: list[str] = []
    for i in range(features.shape[1]):
        column = features[:, i]
        name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
        if np.issubdtype(column.dtype, np.number):
            if np.isnan(column).any():
                columns.append(name)
        elif any(_is_missing(value) for value in column):
            columns.append(name)
    return columns


def _missing_value_message(feature_nan_cols: list[str], target_has_nan: bool) -> str:
    """Build an actionable missing-value error message (FR-169)."""
    parts: list[str] = []
    if feature_nan_cols:
        parts.append("missing values in feature column(s): " + ", ".join(feature_nan_cols))
    if target_has_nan:
        parts.append("missing values in the target column")
    return "Dataset validation failed: " + "; ".join(parts) + "."


def _is_missing(value: object) -> bool:
    """Return True when a scalar cell is empty/NaN-like (FR-169)."""
    if value is None:
        return True
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return True
    if isinstance(value, str):
        return value.strip().lower() in _EMPTY_TOKENS
    return False


def _drop_missing_rows(dataset: Dataset, target_has_nan: bool) -> Dataset:
    """Return a copy of the dataset with missing-value rows removed (FR-170)."""
    features = np.asarray(dataset.features)
    targets = np.asarray(dataset.targets)
    keep = np.ones(features.shape[0], dtype=bool)

    if features.ndim == 2 and features.shape[0] == targets.shape[0]:
        if np.issubdtype(features.dtype, np.number):
            keep &= ~np.isnan(features.astype(np.float64)).any(axis=1)
        else:
            keep &= ~np.array([any(_is_missing(value) for value in row) for row in features])
        if target_has_nan:
            keep &= ~np.array([_is_missing(value) for value in targets])

    return Dataset(
        features=features[keep],
        targets=targets[keep],
        feature_names=list(dataset.feature_names),
        target_names=list(dataset.target_names) if dataset.target_names else None,
        source=dataset.source,
        description=dataset.description,
    )


def _mean_impute(dataset: Dataset) -> tuple[Dataset, list[str], list[str]]:
    """Fill numeric feature NaNs with the column mean (FR-170).

    Returns:
        Tuple of ``(cleaned_dataset, imputed_columns, failed_columns)``.
        Entirely-NaN columns cannot be imputed and are reported as failed so
        the caller can fall back to ``"error"``.

    Raises:
        DatasetValidationError: If features are not numeric.
    """
    try:
        features = np.asarray(dataset.features).astype(np.float64)
    except (TypeError, ValueError) as exc:
        raise DatasetValidationError("'mean_impute' requires numeric feature columns.") from exc

    imputed: list[str] = []
    failed: list[str] = []
    for i in range(features.shape[1]):
        name = dataset.feature_names[i] if i < len(dataset.feature_names) else f"feature_{i}"
        column = features[:, i]
        if not np.isnan(column).any():
            continue
        if np.isnan(column).all():
            failed.append(name)
            continue
        features[np.isnan(column), i] = np.nanmean(column)
        imputed.append(name)

    cleaned = Dataset(
        features=features,
        targets=dataset.targets,
        feature_names=list(dataset.feature_names),
        target_names=list(dataset.target_names) if dataset.target_names else None,
        source=dataset.source,
        description=dataset.description,
    )
    return cleaned, imputed, failed
