"""Dataset loading for the DecodeBot ML Engine (FR-164-FR-168, FR-171-FR-172).

Loads the bundled Iris benchmark dataset via ``sklearn.datasets.load_iris()``
by default, or an arbitrary well-formed CSV via ``pandas.read_csv``, always
returning a normalized ``Dataset`` object. Loaded datasets are cached in
memory for the session (FR-168).

Reference: Week 2 brief — "Load and understand a dataset".
"""

import logging
import os

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris

from .dataset import Dataset, DatasetLoadError, DatasetValidationError

logger = logging.getLogger(__name__)

_IRIS_SOURCE = "iris"
_IRIS_DESCRIPTION = "Iris flower benchmark dataset (150 samples, 4 features, 3 classes)."

_CACHE: dict[str, Dataset] = {}


def load_dataset(
    source: str = _IRIS_SOURCE,
    target_column: str | None = None,
    *,
    use_cache: bool = True,
) -> Dataset:
    """Load a dataset into a normalized ``Dataset`` object (FR-164-FR-166).

    Args:
        source: ``"iris"`` for the bundled benchmark dataset, or a path to a
            CSV file (FR-165).
        target_column: Column name to use as the classification target.
            Required for CSV sources.
        use_cache: When True (default) and the dataset was already loaded this
            session, return the cached object without re-reading the source
            (FR-168). Pass False to force a fresh load.

    Returns:
        A normalized ``Dataset`` whose features have shape
        (n_samples, n_features).

    Raises:
        DatasetLoadError: If the CSV path does not exist or cannot be parsed
            (FR-171).
        DatasetValidationError: If the CSV is missing its target column or
            contains non-numeric feature columns (FR-165).

    Reference: Week 2 brief — "Load and understand a dataset".
    """
    key = _cache_key(source, target_column)
    if use_cache and key in _CACHE:
        logger.info("Returning cached dataset for source %r.", source)
        return _CACHE[key]

    if source == _IRIS_SOURCE:
        dataset = _load_iris()
    else:
        dataset = _load_csv(source, target_column)

    if use_cache:
        _CACHE[key] = dataset

    logger.info("Dataset loaded: %s", dataset.describe())
    return dataset


def render_explore_report(dataset: Dataset) -> str:
    """Render an ``explore``-style dataset report (FR-172).

    Reports shape, feature names, class names, class balance, and per-feature
    min/max/mean/std using only numpy — no plotting required (FR-217 handles
    visualization in a later phase).

    Args:
        dataset: The dataset to describe.

    Returns:
        A human-readable multi-line report string.

    Reference: Week 2 brief — "Load and understand a dataset".
    """
    meta = dataset.describe()
    lines = [
        f"Dataset: {dataset.source}",
        (
            f"Samples: {meta['samples']}  Features: {meta['features']}  "
            f"Classes: {meta['classes']}"
        ),
        f"Class balance ratio: {meta['balance_ratio']:.4f}",
        "Feature names: " + ", ".join(dataset.feature_names),
        "Class names: "
        + (
            ", ".join(dataset.target_names)
            if dataset.target_names
            else ", ".join(str(name) for name in meta["class_counts"])
        ),
        "Class counts: "
        + ", ".join(f"{name}={count}" for name, count in meta["class_counts"].items()),
        "",
        "Per-feature statistics (min / max / mean / std):",
    ]
    for name, stats in dataset.feature_statistics().items():
        lines.append(
            f"  {name}: {stats['min']:.4f} / {stats['max']:.4f} / "
            f"{stats['mean']:.4f} / {stats['std']:.4f}"
        )
    logger.info("Explore report rendered for dataset %r.", dataset.source)
    return "\n".join(lines)


def _cache_key(source: str, target_column: str | None) -> str:
    """Build the in-memory cache key for a source (FR-168)."""
    if source == _IRIS_SOURCE:
        return _IRIS_SOURCE
    return f"{os.path.abspath(source)}::target={target_column}"


def _load_iris() -> Dataset:
    """Load and normalize the Iris benchmark dataset (FR-164)."""
    iris = load_iris()
    features = np.asarray(iris.data, dtype=np.float64)
    targets = np.asarray(iris.target)
    return Dataset(
        features=features,
        targets=targets,
        feature_names=[str(name) for name in iris.feature_names],
        target_names=[str(name) for name in iris.target_names],
        source=_IRIS_SOURCE,
        description=_IRIS_DESCRIPTION,
    )


def _load_csv(path: str, target_column: str | None) -> Dataset:
    """Load and normalize a CSV dataset (FR-165)."""
    if not os.path.isfile(path):
        raise DatasetLoadError(
            "Couldn't find that dataset file — check the path and try again: " f"{path}"
        )
    if target_column is None:
        raise DatasetValidationError(
            "CSV datasets require a target column; pass target_column=... "
            "(or set ml_target_column in the config)."
        )

    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 - surfaced as a friendly error (FR-171)
        raise DatasetLoadError(f"Couldn't parse the dataset file '{path}' as CSV: {exc}") from exc

    if target_column not in frame.columns:
        raise DatasetValidationError(
            f"Target column '{target_column}' not found in '{path}'. "
            f"Available columns: {', '.join(str(col) for col in frame.columns)}"
        )

    feature_names = [str(col) for col in frame.columns if str(col) != target_column]
    non_numeric = [name for name in feature_names if not pd.api.types.is_numeric_dtype(frame[name])]
    if non_numeric:
        raise DatasetValidationError(
            "Non-numeric feature column(s) found: " + ", ".join(non_numeric) + ". "
            "All feature columns must be numeric."
        )

    try:
        features = frame[feature_names].to_numpy(dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise DatasetValidationError(
            "Feature columns could not be converted to numeric values."
        ) from exc

    targets = frame[target_column].to_numpy()

    target_names: list[str] | None = None
    if not pd.api.types.is_numeric_dtype(frame[target_column]):
        unique_values = {str(value) for value in frame[target_column].dropna().unique()}
        target_names = sorted(unique_values)

    description = (
        f"CSV dataset from '{os.path.basename(path)}': "
        f"{features.shape[0]} samples, {features.shape[1]} features."
    )
    return Dataset(
        features=features,
        targets=targets,
        feature_names=feature_names,
        target_names=target_names,
        source=os.path.abspath(path),
        description=description,
    )
