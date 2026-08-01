"""Model training for the ML Engine (FR-187-FR-195).

Trains ``KNeighborsClassifier`` as the required baseline plus a swappable set
of additional classifiers behind one interface, tracks training duration,
validates inputs with friendly errors, tunes K via the elbow method, and
exposes a deterministic retraining path for regression tests.

Reference: Week 2 brief — "Apply a simple classification algorithm",
"Tuning the Engine: Choosing K".
"""

import logging
import time
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from .dataset import Dataset, DatasetError
from .dataset_validator import validate_dataset
from .preprocessor import (
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    preprocess_and_split,
)

logger = logging.getLogger(__name__)

CLASSIFIER_TYPES: tuple[str, ...] = (
    "knn",
    "decision_tree",
    "logistic_regression",
    "svm",
    "random_forest",
)
DEFAULT_CLASSIFIER_TYPE: str = "knn"
DEFAULT_KNN_K: int = 5
DEFAULT_K_RANGE = range(1, 21)


class TrainingError(DatasetError):
    """Raised for invalid training configuration or input (FR-187, FR-193)."""


@dataclass
class TrainingResult:
    """Outcome of a single ``Trainer.train()`` call (FR-189, FR-192, FR-195).

    Attributes:
        model: The fitted scikit-learn classifier.
        classifier_type: The classifier key used (FR-191).
        knn_k: The K value used for KNN; None for other classifiers (FR-188).
        random_state: The reproducibility seed used (FR-178, FR-195).
        n_samples: Number of training samples.
        n_features: Number of features.
        duration_ms: Training wall-clock time in milliseconds (FR-192).
        classes: The model's known class labels (``model.classes_``).
    """

    model: object
    classifier_type: str
    knn_k: int | None
    random_state: int
    n_samples: int
    n_features: int
    duration_ms: float
    classes: list

    def summary(self) -> str:
        """Return the one-line training summary (FR-192, FR-194)."""
        classifier = (
            f"knn(k={self.knn_k})" if self.classifier_type == "knn" else self.classifier_type
        )
        return (
            f"Model trained in {self.duration_ms:.0f}ms. Classifier: {classifier} | "
            f"Samples: {self.n_samples} | Features: {self.n_features} | "
            f"Classes: {self.classes}"
        )


@dataclass
class TuneResult:
    """Outcome of the K-tuning elbow scan (FR-190).

    Attributes:
        scores: List of ``(k, error_rate)`` pairs for each valid K scanned.
        best_k: The K with the lowest error rate (smallest K on ties).
        best_error_rate: Error rate at ``best_k``.
    """

    scores: list[tuple[int, float]]
    best_k: int
    best_error_rate: float


@dataclass
class TrainRunReport:
    """Full-pipeline report from ``train_pipeline`` (FR-194).

    Attributes:
        dataset_source: Source identifier of the trained dataset.
        dataset_samples: Total sample count before splitting.
        dataset_features: Feature count.
        n_train: Training set size.
        n_test: Test set size.
        training_result: The ``TrainingResult`` from the final fit.
    """

    dataset_source: str
    dataset_samples: int
    dataset_features: int
    n_train: int
    n_test: int
    training_result: TrainingResult

    def summary(self) -> str:
        """Return the multi-line FR-194 summary."""
        return "\n".join(
            [
                f"Dataset: {self.dataset_source} "
                f"({self.dataset_samples} samples, {self.dataset_features} features)",
                f"Training set: {self.n_train} samples | Test set: {self.n_test} samples",
                self.training_result.summary(),
            ]
        )


class Trainer:
    """Trains scikit-learn classifiers behind one interface (FR-187-FR-195).

    The default classifier is ``KNeighborsClassifier`` with ``n_neighbors=5``,
    matching the Week 2 brief's exact ``INSTANTIATE -> FIT -> PREDICT``
    workflow (FR-187, FR-188). Additional classifiers are swappable via
    ``classifier_type`` (FR-191).
    """

    def __init__(
        self,
        *,
        classifier_type: str = DEFAULT_CLASSIFIER_TYPE,
        knn_k: int = DEFAULT_KNN_K,
        random_state: int = DEFAULT_RANDOM_STATE,
    ) -> None:
        if classifier_type not in CLASSIFIER_TYPES:
            logger.warning(
                "Unknown classifier_type %r; falling back to 'knn' (FR-191).",
                classifier_type,
            )
            classifier_type = DEFAULT_CLASSIFIER_TYPE
        if not isinstance(knn_k, int) or isinstance(knn_k, bool) or knn_k < 1:
            raise TrainingError(
                f"knn_k must be a positive integer; got {knn_k!r}. " "Check the knn_k config value."
            )
        self.classifier_type = classifier_type
        self.knn_k = knn_k
        self.random_state = random_state

    def train(self, X_train, y_train) -> TrainingResult:
        """Fit the configured classifier and report duration (FR-189, FR-192).

        Args:
            X_train: 2-D numeric training features (n_samples, n_features).
            y_train: Training target labels of length n_samples.

        Returns:
            A ``TrainingResult`` containing the fitted model and timing.

        Raises:
            TrainingError: For malformed input, an invalid K for the data
                size, or an insufficient number of classes (FR-187, FR-193).
        """
        X = self._coerce_features(X_train)
        y = np.asarray(y_train)
        self._validate_shapes(X, y)
        if self.classifier_type == "knn" and self.knn_k > X.shape[0]:
            raise TrainingError(
                f"knn_k ({self.knn_k}) is larger than the training set "
                f"({X.shape[0]} samples). Reduce knn_k or add more data."
            )
        if len(np.unique(y)) < 2:
            raise TrainingError("At least 2 distinct classes are required to train a classifier.")

        model = _build_classifier(self.classifier_type, self.knn_k, self.random_state)
        start = time.perf_counter()
        model.fit(X, y)
        duration_ms = (time.perf_counter() - start) * 1000.0

        logger.info(
            "Trained %s on %d samples in %.0fms.",
            self.classifier_type,
            X.shape[0],
            duration_ms,
        )
        return TrainingResult(
            model=model,
            classifier_type=self.classifier_type,
            knn_k=self.knn_k if self.classifier_type == "knn" else None,
            random_state=self.random_state,
            n_samples=int(X.shape[0]),
            n_features=int(X.shape[1]),
            duration_ms=duration_ms,
            classes=[_plain(value) for value in model.classes_],
        )

    def tune_k(
        self,
        X_train,
        y_train,
        X_test,
        y_test,
        *,
        k_range=DEFAULT_K_RANGE,
    ) -> TuneResult:
        """Scan K values with the elbow method (FR-190).

        Trains a KNN classifier for every valid K in ``k_range`` and computes
        the test-set error rate for each. The best K is the one with the
        lowest error rate; ties are broken toward the smallest K.

        Args:
            X_train: 2-D numeric training features.
            y_train: Training target labels.
            X_test: 2-D numeric test features.
            y_test: Test target labels.
            k_range: Iterable of K values to scan (default ``range(1, 21)``).
                Values outside ``1 <= k <= len(X_train)`` are skipped with a
                logged warning.

        Returns:
            A ``TuneResult`` with the ``(k, error_rate)`` scores and best K.

        Raises:
            TrainingError: If ``k_range`` contains no valid K values.
        """
        X_train = self._coerce_features(X_train)
        X_test = self._coerce_features(X_test)
        y_train = np.asarray(y_train)
        y_test = np.asarray(y_test)
        self._validate_shapes(X_train, y_train)
        self._validate_shapes(X_test, y_test)

        valid_k: list[int] = []
        skipped_k: list[int] = []
        for k in k_range:
            if isinstance(k, (int, np.integer)) and 1 <= int(k) <= X_train.shape[0]:
                valid_k.append(int(k))
            else:
                skipped_k.append(k)
        if not valid_k:
            raise TrainingError(
                f"k_range contains no valid K values (1 <= k <= training set "
                f"size {X_train.shape[0]}); got {list(k_range)!r}."
            )
        if skipped_k:
            logger.warning(
                "Skipping out-of-range K value(s) %s; training set has %d samples.",
                skipped_k,
                X_train.shape[0],
            )

        scores: list[tuple[int, float]] = []
        for k in valid_k:
            model = KNeighborsClassifier(n_neighbors=k)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            error_rate = 1.0 - float(accuracy_score(y_test, predictions))
            scores.append((k, error_rate))

        best_k, best_error_rate = min(scores, key=lambda pair: (pair[1], pair[0]))
        logger.info("K-tuning: best K=%d with error rate %.4f.", best_k, best_error_rate)
        return TuneResult(scores=scores, best_k=best_k, best_error_rate=best_error_rate)

    def _coerce_features(self, X) -> np.ndarray:
        """Return X as a float64 ndarray or raise a friendly TrainingError."""
        try:
            return np.asarray(X, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise TrainingError("Features must be numeric.") from exc

    def _validate_shapes(self, X: np.ndarray, y: np.ndarray) -> None:
        """Validate feature dimensionality and row-count agreement (FR-193)."""
        if X.ndim != 2:
            raise TrainingError(
                f"Features must be 2-dimensional (samples x features); got {X.ndim}D."
            )
        if X.shape[0] != y.shape[0]:
            raise TrainingError(
                f"Row count mismatch: X has {X.shape[0]} rows but y has {y.shape[0]}."
            )


def _build_classifier(classifier_type: str, knn_k: int, random_state: int):
    """Instantiate the requested classifier with reproducibility-aware args."""
    if classifier_type == "knn":
        return KNeighborsClassifier(n_neighbors=knn_k)
    if classifier_type == "decision_tree":
        return DecisionTreeClassifier(random_state=random_state)
    if classifier_type == "logistic_regression":
        return LogisticRegression(random_state=random_state)
    if classifier_type == "svm":
        return SVC(random_state=random_state)
    return RandomForestClassifier(random_state=random_state)


def _plain(value):
    """Convert a numpy scalar to its native Python equivalent for output."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.str_):
        return str(value)
    return value


def train_pipeline(
    dataset: Dataset,
    *,
    scaler_type: str = "standard",
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    classifier_type: str = DEFAULT_CLASSIFIER_TYPE,
    knn_k: int = DEFAULT_KNN_K,
    shuffle: bool = True,
    stratify: bool = True,
) -> TrainRunReport:
    """Run the full training pipeline: validate -> preprocess -> split -> train (FR-194).

    This is the ``train`` command scaffold: the loader step (``load_dataset``)
    is performed by the caller, and the full CLI/GUI wiring lands in Phase 21.
    With defaults this trains ``KNeighborsClassifier(n_neighbors=5)`` on Iris
    and reports a summary including dataset size, split sizes, chosen
    K/classifier, and training time.

    Args:
        dataset: A loaded ``Dataset``.
        scaler_type: Scaler to use in preprocessing (FR-175).
        test_size: Fraction of samples held out for testing (FR-182).
        random_state: Reproducibility seed (FR-178, FR-195).
        classifier_type: Classifier key (FR-191); default ``"knn"``.
        knn_k: Neighbor count for KNN (FR-188); default 5.
        shuffle: Whether to shuffle before splitting (FR-177).
        stratify: Whether to stratify the split (FR-183).

    Returns:
        A ``TrainRunReport`` summarizing the run.

    Raises:
        DatasetValidationError: If the dataset fails integrity validation.
        TrainingError: For invalid hyperparameters or malformed input.
    """
    cleaned, _ = validate_dataset(dataset)
    split = preprocess_and_split(
        cleaned,
        scaler_type=scaler_type,
        test_size=test_size,
        random_state=random_state,
        shuffle=shuffle,
        stratify=stratify,
    )
    training = Trainer(
        classifier_type=classifier_type,
        knn_k=knn_k,
        random_state=random_state,
    ).train(split.X_train, split.y_train)

    logger.info("train pipeline complete for %s: %s", cleaned.source, training.summary())
    return TrainRunReport(
        dataset_source=cleaned.source,
        dataset_samples=int(cleaned.features.shape[0]),
        dataset_features=int(cleaned.features.shape[1]),
        n_train=split.split_report.n_train,
        n_test=split.split_report.n_test,
        training_result=training,
    )
