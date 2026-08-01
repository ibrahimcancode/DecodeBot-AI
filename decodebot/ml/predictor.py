"""Prediction interface for the ML Engine (FR-196-FR-200).

Provides batch prediction on a test set (``Predictor.predict``), single-sample
live classification (``Predictor.predict_one``), optional per-class
probability output where the classifier supports it, a friendly guard when no
trained model exists, and a readable prediction-results table for CLI/GUI
review.

Reference: Week 2 brief — "Prediction" and the canonical Iris example
``[5.1, 3.5, 1.4, 0.2]`` -> ``"setosa"``.
"""

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.exceptions import NotFittedError

from .dataset import DatasetError

logger = logging.getLogger(__name__)

NO_MODEL_MESSAGE = "No trained model found — run 'train' first."


class PredictorError(DatasetError):
    """Raised for invalid prediction input or a missing trained model (FR-197, FR-199)."""


@dataclass
class SinglePrediction:
    """Outcome of a single-sample prediction (FR-197, FR-198).

    Attributes:
        label: The predicted class label (decoded to a name when a label
            mapping is available).
        probabilities: Per-class probability mapping (name -> probability)
            summing to 1.0, or None when the classifier does not expose
            ``predict_proba``.
    """

    label: str
    probabilities: dict[str, float] | None


class Predictor:
    """Predicts class labels from a trained model (FR-196-FR-200).

    Args:
        class_names: Optional human-readable class names aligned by integer
            class code (e.g. ``Dataset.target_names``, or the sorted labels a
            ``LabelEncoder`` produced). When provided, predicted codes are
            decoded back to their names (``predict_one`` returns ``"setosa"``
            for the canonical Iris sample).
        preprocessor: Optional fitted ``Preprocessor``. When provided,
            ``predict_one`` scales raw feature values through the identical
            train-time scaling before classification, so users may type raw
            feature values directly.
    """

    def __init__(self, class_names: list[str] | None = None, preprocessor=None) -> None:
        self.class_names = list(class_names) if class_names else None
        self.preprocessor = preprocessor

    def predict(self, model, X):
        """Predict class labels for a full test set in one call (FR-196).

        Args:
            model: A fitted scikit-learn classifier, or None if no model has
                been trained (FR-199).
            X: Already-preprocessed test features of shape (n_samples,
                n_features) — e.g. ``PreprocessResult.X_test``.

        Returns:
            A numpy array of predicted class labels with length equal to
            ``len(X)``. Labels are decoded to class names when ``class_names``
            is configured.

        Raises:
            PredictorError: If no trained model exists, the model is not
                fitted, or the feature matrix is malformed.
        """
        if model is None:
            raise PredictorError(NO_MODEL_MESSAGE)
        X = self._coerce_batch_features(model, X)
        predictions = self._predict_safe(model, X)
        return self._decode(predictions)

    def predict_one(
        self,
        model,
        features,
        *,
        return_proba: bool = False,
    ) -> str | SinglePrediction:
        """Classify a single new sample (FR-197, FR-198).

        Args:
            model: A fitted scikit-learn classifier, or None (FR-199).
            features: A sequence of feature values, e.g. ``[5.1, 3.5, 1.4,
                0.2]`` for Iris. Raw feature values are scaled through the
                configured preprocessor before classification.
            return_proba: When True, return a ``SinglePrediction`` carrying
                the predicted label and the per-class probability
                distribution (FR-198).

        Returns:
            The predicted class label by default (``"setosa"`` for the
            canonical Iris sample), or a ``SinglePrediction`` when
            ``return_proba`` is True.

        Raises:
            PredictorError: If no trained model exists, the model is not
                fitted, or the feature vector has the wrong dimensionality.
        """
        if model is None:
            raise PredictorError(NO_MODEL_MESSAGE)
        sample = self._coerce_single_sample(model, features)
        scaled, _ = self._transform_sample(sample)
        prediction = self._predict_safe(model, scaled[np.newaxis, :])[0]

        label = self._decode(np.asarray([prediction]))[0]
        if not return_proba:
            return label

        probabilities = self._probabilities(model, scaled)
        return SinglePrediction(label=label, probabilities=probabilities)

    def _coerce_batch_features(self, model, X) -> np.ndarray:
        """Validate and return a 2-D float feature matrix (FR-196 edge)."""
        try:
            arr = np.asarray(X, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise PredictorError("Features must be numeric.") from exc
        if arr.ndim != 2:
            raise PredictorError(
                f"Features must be 2-dimensional (samples x features); got {arr.ndim}D."
            )
        self._check_feature_width(model, arr.shape[1])
        return arr

    def _coerce_single_sample(self, model, features) -> np.ndarray:
        """Validate and return a single 1-D float feature vector (FR-197 edge)."""
        try:
            arr = np.asarray(features, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise PredictorError("Features must be numeric.") from exc
        if arr.ndim != 1:
            raise PredictorError(f"Single-sample features must be 1-dimensional; got {arr.ndim}D.")
        self._check_feature_width(model, arr.shape[0])
        return arr

    def _check_feature_width(self, model, width: int) -> None:
        """Reject feature vectors whose width differs from the model's (FR-197)."""
        expected = getattr(model, "n_features_in_", None)
        if expected is not None and width != int(expected):
            raise PredictorError(
                f"Expected {int(expected)} feature value(s), got {width}. "
                "Check the number of feature values you entered."
            )

    def _transform_sample(self, sample: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        """Scale a raw sample through the preprocessor when one is configured."""
        if self.preprocessor is None:
            return sample, None
        scaled, encoded = self.preprocessor.transform(sample.reshape(1, -1))
        return scaled[0], encoded

    def _predict_safe(self, model, X) -> np.ndarray:
        """Run ``model.predict``, converting a NotFittedError to a friendly one."""
        try:
            return np.asarray(model.predict(X))
        except NotFittedError as exc:
            raise PredictorError(NO_MODEL_MESSAGE) from exc

    def _probabilities(self, model, sample: np.ndarray) -> dict[str, float] | None:
        """Return per-class probabilities when supported, else None (FR-198)."""
        predict_proba = getattr(model, "predict_proba", None)
        if not callable(predict_proba):
            logger.info(
                "Classifier %s does not support predict_proba; omitting probabilities.",
                type(model).__name__,
            )
            return None
        probs = np.asarray(predict_proba(sample.reshape(1, -1)))[0]
        classes = getattr(model, "classes_", None)
        if classes is None:
            return {str(i): _plain(float(value)) for i, value in enumerate(probs)}
        return {self._class_name(code): _plain(float(value)) for code, value in zip(classes, probs)}

    def _decode(self, predictions: np.ndarray) -> np.ndarray:
        """Decode predicted codes to class names when ``class_names`` is set."""
        plain = [_plain(value) for value in predictions]
        if not self.class_names:
            return np.asarray(plain)
        decoded = []
        for value in plain:
            try:
                index = int(value)
            except (TypeError, ValueError):
                decoded.append(str(value))
                continue
            if 0 <= index < len(self.class_names):
                decoded.append(self.class_names[index])
            else:
                decoded.append(str(value))
        return np.asarray(decoded)

    def _class_name(self, code) -> str:
        """Return the human-readable name for a single predicted code."""
        try:
            index = int(code)
        except (TypeError, ValueError):
            return str(_plain(code))
        if self.class_names and 0 <= index < len(self.class_names):
            return self.class_names[index]
        return str(_plain(code))


def render_prediction_table(
    predictions,
    y_true=None,
    *,
    sample_indices=None,
) -> str:
    """Format batch predictions as a simple table (FR-200).

    Args:
        predictions: Iterable of predicted class labels.
        y_true: Optional true labels; when provided the table gains a
            correct/incorrect flag column.
        sample_indices: Optional 0-based sample indices; defaults to
            ``range(len(predictions))``.

    Returns:
        A fixed-width table string with a sample index, predicted class, and
        (when available) true class and correct/incorrect columns.
    """
    predicted = [_plain(value) for value in predictions]
    truth = [_plain(value) for value in y_true] if y_true is not None else None
    indices = list(sample_indices) if sample_indices is not None else range(len(predicted))

    if truth is not None:
        rows = [
            (str(i), str(p), str(t), "Yes" if p == t else "No")
            for i, p, t in zip(indices, predicted, truth)
        ]
        header = ("Idx", "Predicted", "True", "Correct?")
    else:
        rows = [(str(i), str(p)) for i, p in zip(indices, predicted)]
        header = ("Idx", "Predicted")
    if truth is not None:
        header = ("Idx", "Predicted", "True", "Correct?")

    col_width = [
        max(len(header[i]), max((len(row[i]) for row in rows), default=0))
        for i in range(len(header))
    ]
    lines = ["  ".join(str(header[i]).ljust(col_width[i]) for i in range(len(header)))]
    lines.append("  ".join("-" * width for width in col_width))
    lines.extend("  ".join(row[i].ljust(col_width[i]) for i in range(len(header))) for row in rows)
    return "\n".join(lines)


def _plain(value):
    """Convert a numpy scalar to its native Python equivalent for output."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.str_):
        return str(value)
    return value
