"""Preprocessing and train/test splitting (FR-173-FR-186).

Scales numeric features with a train-only fit discipline, encodes string
target labels, shuffles and splits data into stratified training/test sets,
and composes the preprocessing steps into a ``sklearn.pipeline.Pipeline``.

Reference: Week 2 brief — "Gatekeeper Rule: Scaling" and "Structural
Integrity: The Split".
"""

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from .dataset import Dataset, DatasetError

logger = logging.getLogger(__name__)

SCALER_TYPES: tuple[str, ...] = ("standard", "minmax", "none")
DEFAULT_TEST_SIZE: float = 0.2
DEFAULT_RANDOM_STATE: int = 42


class PreprocessingError(DatasetError):
    """Raised for invalid preprocessing/split configuration (FR-182)."""


@dataclass
class PreprocessingReport:
    """Before/after summary of a preprocessing pass (FR-180).

    Attributes:
        scaler_used: The active scaler type (``"standard"``/``"minmax"``/``"none"``).
        encoded_targets: Whether string targets were LabelEncoder-encoded (FR-176).
        label_mapping: Encoded label mapping (label -> code), or None.
        features_before: Per-feature min/max ranges before scaling.
        features_after: Per-feature min/max ranges after scaling.
    """

    scaler_used: str
    encoded_targets: bool
    label_mapping: dict[str, int] | None
    features_before: dict[str, dict[str, float]]
    features_after: dict[str, dict[str, float]]


@dataclass
class SplitReport:
    """Summary of a train/test split (FR-186).

    Attributes:
        test_size: Fraction of samples held out for testing.
        random_state: Seed used for shuffling and splitting (FR-178).
        shuffled: Whether data was shuffled before splitting (FR-177).
        stratified: Whether the split preserved class proportions (FR-183).
        n_train: Number of training samples.
        n_test: Number of test samples.
        train_class_counts: Per-class counts in the training set.
        test_class_counts: Per-class counts in the test set.
    """

    test_size: float
    random_state: int
    shuffled: bool
    stratified: bool
    n_train: int
    n_test: int
    train_class_counts: dict[str, int]
    test_class_counts: dict[str, int]

    def summary(self) -> str:
        """Return the one-line split summary (FR-186 acceptance criteria)."""
        return f"Training set: {self.n_train} samples | Test set: {self.n_test} samples"


@dataclass
class PreprocessResult:
    """Output of ``preprocess_and_split`` (FR-173-FR-186).

    Attributes:
        preprocessor: The fitted Preprocessor (scaler + optional encoder).
        X_train: Scaled training features, shape (n_train, n_features).
        X_test: Scaled test features, shape (n_test, n_features).
        y_train: Training targets (integer-encoded when labels were strings).
        y_test: Test targets (integer-encoded when labels were strings).
        report: Preprocessing before/after report (FR-180).
        split_report: Split summary (FR-186).
    """

    preprocessor: "Preprocessor"
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    report: PreprocessingReport
    split_report: SplitReport


class Preprocessor:
    """Scales numeric features and encodes string targets (FR-173-FR-181).

    The scaler is fit **only** on the training set and reused to transform any
    downstream input, preventing data leakage (FR-174, FR-184). All operations
    work on copies so the caller's arrays are never mutated (FR-181).
    """

    def __init__(
        self,
        scaler_type: str = "standard",
        *,
        random_state: int = DEFAULT_RANDOM_STATE,
        shuffle: bool = True,
    ) -> None:
        if scaler_type not in SCALER_TYPES:
            logger.warning(
                "Unknown scaler_type %r; falling back to 'standard' (FR-175).",
                scaler_type,
            )
            scaler_type = "standard"
        self.scaler_type = scaler_type
        self.random_state = random_state
        self.shuffle = shuffle
        self._scaler: StandardScaler | MinMaxScaler | None = None
        self._label_encoder: LabelEncoder | None = None
        self._fitted = False

    def fit(self, features, targets=None) -> "Preprocessor":
        """Fit the scaler on ``features`` and the encoder on ``targets``.

        Args:
            features: 2-D numeric training features (n_train, n_features).
            targets: Optional target labels; string labels are
                LabelEncoder-encoded (FR-176), numeric labels pass through
                unchanged.

        Returns:
            ``self`` (fitted).

        Raises:
            PreprocessingError: If ``features`` is not 2-dimensional.
        """
        train_features = np.array(features, dtype=np.float64, copy=True)
        if train_features.ndim != 2:
            raise PreprocessingError(
                f"Features must be 2-dimensional (samples x features); "
                f"got {train_features.ndim}D."
            )

        if self.scaler_type == "none":
            self._scaler = None
        else:
            self._scaler = StandardScaler() if self.scaler_type == "standard" else MinMaxScaler()
            self._scaler.fit(train_features)  # train-only fit (FR-174, FR-184)

        self._label_encoder = None
        if targets is not None and _needs_encoding(targets):
            self._label_encoder = LabelEncoder()
            self._label_encoder.fit(np.asarray(targets))

        self._fitted = True
        return self

    def transform(self, features, targets=None) -> tuple[np.ndarray, np.ndarray | None]:
        """Scale ``features`` and encode ``targets`` using the fitted state.

        Args:
            features: 2-D numeric features to transform.
            targets: Optional target labels to encode.

        Returns:
            A ``(scaled_features, encoded_targets)`` tuple; ``encoded_targets``
            is None when no targets were supplied.

        Raises:
            PreprocessingError: If the preprocessor has not been fitted.
        """
        if not self._fitted:
            raise PreprocessingError("Preprocessor must be fitted before transform().")
        scaled = np.array(features, dtype=np.float64, copy=True)
        if self._scaler is not None:
            scaled = self._scaler.transform(scaled)

        encoded = None
        if targets is not None:
            if self._label_encoder is not None:
                encoded = self._label_encoder.transform(np.asarray(targets))
            else:
                encoded = np.asarray(targets)
        return scaled, encoded

    def fit_transform(self, features, targets=None) -> tuple[np.ndarray, np.ndarray | None]:
        """Fit on ``features``/``targets`` then transform them (train-only)."""
        return self.fit(features, targets).transform(features, targets)

    def inverse_transform_labels(self, labels) -> np.ndarray:
        """Map integer labels back to human-readable names (FR-176)."""
        if self._label_encoder is None:
            return np.asarray(labels)
        return self._label_encoder.inverse_transform(np.asarray(labels))

    @property
    def scaler(self) -> StandardScaler | MinMaxScaler | None:
        """The fitted scikit-learn scaler, or None for ``"none"``."""
        return self._scaler

    @property
    def label_encoder(self) -> LabelEncoder | None:
        """The fitted LabelEncoder, or None when no encoding was needed."""
        return self._label_encoder

    @property
    def pipeline(self) -> Pipeline:
        """A ``sklearn.pipeline.Pipeline`` composing the fitted steps (FR-179).

        The pipeline applies the identical scaling used during training to any
        raw sample, so a later-phase model can be appended as the final step.

        Raises:
            PreprocessingError: If the preprocessor has not been fitted.
        """
        if not self._fitted:
            raise PreprocessingError("Cannot build a pipeline before fitting the preprocessor.")
        steps = []
        if self._scaler is not None:
            steps.append(("scaler", self._scaler))
        return Pipeline(steps)


def preprocess_and_split(
    dataset: Dataset,
    *,
    scaler_type: str = "standard",
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    shuffle: bool = True,
    stratify: bool = True,
) -> PreprocessResult:
    """Scale, shuffle, and split a dataset into training/test sets (FR-173-FR-186).

    Args:
        dataset: A validated ``Dataset`` from ``load_dataset()``.
        scaler_type: ``"standard"`` (default), ``"minmax"``, or ``"none"``
            (FR-175). An unknown value falls back to ``"standard"`` with a
            logged warning.
        test_size: Fraction of samples held out for testing (default 0.2).
            Must be strictly between 0 and 1 (FR-182).
        random_state: Reproducibility seed for shuffling and splitting (FR-178).
        shuffle: Whether to shuffle before splitting (default True; FR-177).
            ``False`` is an explicit opt-out for debugging/determinism checks.
        stratify: Whether to preserve class proportions (default True; FR-183).
            Automatically disabled with a logged warning when a class has
            fewer than 2 samples, or when ``shuffle=False``.

    Returns:
        A ``PreprocessResult`` with scaled, split arrays and both reports.

    Raises:
        PreprocessingError: For an invalid ``test_size`` or malformed features.

    Reference: Week 2 brief — "Gatekeeper Rule: Scaling", "Structural
    Integrity: The Split".
    """
    if not 0.0 < float(test_size) < 1.0:
        raise PreprocessingError(
            f"test_size must be between 0 and 1 (exclusive); got {test_size!r}. "
            "Check the ml_test_size config value."
        )

    features = np.array(dataset.features, dtype=np.float64, copy=True)
    targets = np.asarray(dataset.targets)
    if features.ndim != 2:
        raise PreprocessingError(
            f"Feature matrix must be 2-dimensional (samples x features); " f"got {features.ndim}D."
        )
    if features.shape[0] != targets.shape[0]:
        raise PreprocessingError(
            f"Row count mismatch: features have {features.shape[0]} rows but "
            f"targets have {targets.shape[0]}."
        )

    stratified_used = bool(stratify)
    split_stratify = targets if stratified_used else None
    if stratified_used and _smallest_class(targets) < 2:
        logger.warning("Stratified splitting disabled: a class has fewer than 2 samples.")
        stratified_used = False
        split_stratify = None
    if not shuffle and stratified_used:
        logger.warning(
            "Stratified splitting disabled: shuffle=False is incompatible " "with stratification."
        )
        stratified_used = False
        split_stratify = None

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        targets,
        test_size=float(test_size),
        random_state=int(random_state),
        shuffle=shuffle,
        stratify=split_stratify,
    )

    preprocessor = Preprocessor(scaler_type=scaler_type, random_state=random_state, shuffle=shuffle)
    features_before = _feature_ranges(X_train, dataset.feature_names)
    X_train_scaled, y_train_encoded = preprocessor.fit_transform(X_train, y_train)
    X_test_scaled, y_test_encoded = preprocessor.transform(X_test, y_test)
    features_after = _feature_ranges(X_train_scaled, dataset.feature_names)

    label_mapping: dict[str, int] | None = None
    if preprocessor.label_encoder is not None:
        classes = preprocessor.label_encoder.classes_
        label_mapping = {
            str(label): int(code)
            for label, code in zip(classes, preprocessor.label_encoder.transform(classes))
        }

    report = PreprocessingReport(
        scaler_used=preprocessor.scaler_type,
        encoded_targets=preprocessor.label_encoder is not None,
        label_mapping=label_mapping,
        features_before=features_before,
        features_after=features_after,
    )

    split_report = SplitReport(
        test_size=float(test_size),
        random_state=int(random_state),
        shuffled=shuffle,
        stratified=stratified_used,
        n_train=int(X_train_scaled.shape[0]),
        n_test=int(X_test_scaled.shape[0]),
        train_class_counts=_class_counts(y_train_encoded, dataset, preprocessor),
        test_class_counts=_class_counts(y_test_encoded, dataset, preprocessor),
    )

    logger.info(
        "Preprocessed %s: %s; scaler=%s, stratified=%s.",
        dataset.source,
        split_report.summary(),
        preprocessor.scaler_type,
        stratified_used,
    )
    return PreprocessResult(
        preprocessor=preprocessor,
        X_train=X_train_scaled,
        X_test=X_test_scaled,
        y_train=y_train_encoded,
        y_test=y_test_encoded,
        report=report,
        split_report=split_report,
    )


def _needs_encoding(targets) -> bool:
    """Return True when targets carry non-numeric labels (FR-176)."""
    return np.asarray(targets).dtype.kind not in "iufb"


def _smallest_class(targets) -> int:
    """Return the smallest per-class sample count, or 0 for empty targets."""
    _, counts = np.unique(np.asarray(targets), return_counts=True)
    return int(counts.min()) if counts.size else 0


def _feature_ranges(features, feature_names) -> dict[str, dict[str, float]]:
    """Return per-feature min/max ranges for a feature matrix (FR-180)."""
    arr = np.asarray(features)
    ranges: dict[str, dict[str, float]] = {}
    for i in range(arr.shape[1]):
        name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
        ranges[name] = {
            "min": float(np.min(arr[:, i])),
            "max": float(np.max(arr[:, i])),
        }
    return ranges


def _class_counts(labels, dataset: Dataset, preprocessor: Preprocessor) -> dict[str, int]:
    """Return per-class counts keyed by human-readable class name (FR-186)."""
    counts: dict[str, int] = {}
    for value in np.asarray(labels):
        name = _label_name(value, dataset, preprocessor)
        counts[name] = counts.get(name, 0) + 1
    return counts


def _label_name(value, dataset: Dataset, preprocessor: Preprocessor) -> str:
    """Map a single encoded/numeric label to its human-readable name."""
    if preprocessor.label_encoder is not None:
        return str(preprocessor.label_encoder.inverse_transform(np.asarray([value]))[0])
    if dataset.target_names is not None:
        try:
            index = int(value)
        except (TypeError, ValueError):
            return str(value)
        if 0 <= index < len(dataset.target_names):
            return str(dataset.target_names[index])
    return str(value)
