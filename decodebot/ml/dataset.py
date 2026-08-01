"""Core data structures for the DecodeBot ML Engine (FR-164).

Defines the normalized ``Dataset`` dataclass shared by every module in
``decodebot.ml``, the numpy/pandas type aliases mandated by the Week 2
coding standards, and the exception hierarchy used by the loader and
validator.

Reference: Week 2 brief — "Load and understand a dataset".
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

FeatureMatrix = np.ndarray
"""Numeric feature matrix alias with shape (n_samples, n_features)."""

TargetVector = np.ndarray
"""Target label vector alias with shape (n_samples,)."""

FeatureFrame = pd.DataFrame
"""Optional pandas frame alias for CSV-originated data."""


class DatasetError(Exception):
    """Base exception for all ML dataset failures (FR-171)."""


class DatasetLoadError(DatasetError):
    """Raised when a dataset cannot be located or parsed (FR-171)."""


class DatasetValidationError(DatasetError):
    """Raised when a dataset fails integrity validation (FR-169)."""


@dataclass
class Dataset:
    """Normalized, validated dataset shared by the ML pipeline (FR-164).

    Attributes:
        features: Numeric feature matrix of shape (n_samples, n_features).
        targets: Target labels of shape (n_samples,); integer class ids for
            Iris or raw labels for CSV data (FR-176 encodes CSV string labels
            in a later phase).
        feature_names: Ordered feature column names.
        target_names: Human-readable class names aligned by integer index.
            ``None`` when labels carry no mapping (e.g. numeric CSV targets).
        source: Source identifier — ``"iris"`` or an absolute CSV path.
        description: Human-readable dataset summary.

    Reference: Week 2 brief — "Load and understand a dataset".
    """

    features: FeatureMatrix
    targets: TargetVector
    feature_names: list[str]
    target_names: list[str] | None = None
    source: str = "iris"
    description: str = ""

    def class_counts(self) -> dict[str, int]:
        """Return per-class sample counts keyed by class name (FR-166)."""
        counts: dict[str, int] = {}
        for value in np.asarray(self.targets):
            label = self._label_of(value)
            counts[label] = counts.get(label, 0) + 1
        return counts

    def class_balance(self) -> float:
        """Return the max/min class-count ratio; ``1.0`` = perfectly balanced (FR-167).

        Returns:
            The balance ratio, or ``inf`` when a class has zero samples.

        Reference: Week 2 brief — "Accuracy Mirage" / class imbalance warning.
        """
        counts = list(self.class_counts().values())
        if not counts:
            return 0.0
        max_count = max(counts)
        min_count = min(counts)
        if min_count == 0:
            return float("inf")
        return max_count / min_count

    def describe(self) -> dict[str, object]:
        """Return dataset metadata for inspection and logging (FR-166).

        Returns:
            A dict with ``samples``, ``features``, ``classes``,
            ``class_counts``, and ``balance_ratio`` keys.
        """
        counts = self.class_counts()
        return {
            "samples": int(self.features.shape[0]),
            "features": int(self.features.shape[1]) if self.features.ndim == 2 else 0,
            "classes": len(counts),
            "class_counts": counts,
            "balance_ratio": self.class_balance(),
        }

    def feature_statistics(self) -> dict[str, dict[str, float]]:
        """Return per-feature min/max/mean/std statistics (FR-172).

        Returns:
            A dict mapping each feature name to its ``min``, ``max``,
            ``mean``, and ``std`` values.

        Raises:
            ValueError: If features contain non-numeric values.
        """
        arr = np.asarray(self.features, dtype=np.float64)
        stats: dict[str, dict[str, float]] = {}
        for i in range(arr.shape[1]):
            column = arr[:, i]
            name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
            stats[name] = {
                "min": float(np.min(column)),
                "max": float(np.max(column)),
                "mean": float(np.mean(column)),
                "std": float(np.std(column)),
            }
        return stats

    def _label_of(self, value: object) -> str:
        """Map a single target value to its human-readable class name."""
        if self.target_names is not None:
            try:
                index = int(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return str(value)
            if 0 <= index < len(self.target_names):
                return str(self.target_names[index])
            return str(value)
        return str(value)
