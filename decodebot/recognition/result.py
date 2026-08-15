"""Recognition result data model, statuses and rendering helpers (FR-257, FR-258).

The engine returns exactly one :class:`RecognitionResult` per run carrying one
of the four FR-257 statuses — ``accepted``, ``low_confidence``, ``no_text`` or
``error`` — together with the confidence-filtered text (FR-256), the pre-filter
``full_text``, the accepted words (with per-word confidence and bounding box),
the separately reported low-confidence words, and engine metadata (image path,
PSM, threshold, duration, deskew outcome). The pure formatting helpers here
(``format_confidence``, ``confidence_range_text``) are shared by the CLI
(FR-258) and the GUI (FR-260) so presentation never re-implements engine logic.

This module depends only on the Python standard library at runtime; the
``processed_image`` field is an opaque reference (an OpenCV ``numpy`` array)
and is deliberately excluded from equality/repr so the frozen dataclass stays
cheap and deterministic.

Reference: SPEC.md Part IV — Categories T5-T6 (FR-256-FR-258).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

STATUS_ACCEPTED = "accepted"
STATUS_LOW_CONFIDENCE = "low_confidence"
STATUS_NO_TEXT = "no_text"
STATUS_ERROR = "error"
"""The four FR-257 recognition statuses, exactly as rendered to users."""

ALL_STATUSES: tuple[str, ...] = (
    STATUS_ACCEPTED,
    STATUS_LOW_CONFIDENCE,
    STATUS_NO_TEXT,
    STATUS_ERROR,
)

STATUS_LABELS: dict[str, str] = {
    STATUS_ACCEPTED: "Accepted",
    STATUS_LOW_CONFIDENCE: "Low confidence",
    STATUS_NO_TEXT: "No text",
    STATUS_ERROR: "Error",
}
"""Human-readable status labels for CLI/GUI rendering (FR-257, FR-258)."""


@dataclass(frozen=True)
class Word:
    """One OCR word with its confidence and bounding box (FR-254, FR-256).

    Attributes:
        text: The recognised word text (already stripped).
        confidence: Normalised per-word confidence in ``0.0-1.0``, or ``None``
            when Tesseract reported no usable confidence (sentinel/parse
            failure) — such words are never treated as accepted evidence
            (FR-256).
        bbox: ``(left, top, width, height)`` pixel box when provided by
            Tesseract, otherwise an empty tuple.
        order: Reading-order index across all words produced by one OCR run.
        block, line: Tesseract block/line numbers used for stable ordering.

    Reference: SPEC.md Part IV — FR-254, FR-256.
    """

    text: str
    confidence: Optional[float] = None
    bbox: Tuple[int, int, int, int] = ()
    order: int = 0
    block: int = 0
    line: int = 0


@dataclass(frozen=True)
class RecognitionResult:
    """A complete recognition run wrapped in a structured result (FR-258).

    Attributes:
        status: One of :data:`STATUS_ACCEPTED`, :data:`STATUS_LOW_CONFIDENCE`,
            :data:`STATUS_NO_TEXT`, :data:`STATUS_ERROR`.
        text: The confidence-filtered accepted text (accepted words joined in
            reading order). Empty for every non-``accepted`` status.
        full_text: The pre-filter full text produced by Tesseract (informational).
        words: Accepted words that passed the confidence threshold (FR-256).
        low_confidence_words: Words with valid but below-threshold confidence,
            reported separately so nothing is silently dropped (FR-256).
        overall_confidence: Arithmetic mean of the accepted words' confidence
            (``None`` when no word was accepted).
        image_path: The local image that was processed.
        psm: The Tesseract page-segmentation mode used (3/6/7/11).
        confidence_threshold: The minimum accepted per-word confidence (0-1).
        duration_ms: Wall-clock duration of the recognition run.
        message: A human-readable message (always present for the ``error``
            status; descriptive for the other statuses).
        deskew_applied, detected_angle: Preprocessing outcome (FR-253).
        processed_image: Opaque reference to the final preprocessed image
            (binary threshold result); ``None`` on the error path. Excluded
            from equality/repr.
        saved_to: Path written by the optional ``--save`` flag, or ``None``.

    Reference: SPEC.md Part IV — Category T6 (FR-258).
    """

    status: str
    text: str = ""
    full_text: str = ""
    words: Tuple[Word, ...] = ()
    low_confidence_words: Tuple[Word, ...] = ()
    overall_confidence: Optional[float] = None
    image_path: str = ""
    psm: int = 6
    confidence_threshold: float = 0.80
    duration_ms: float = 0.0
    message: str = ""
    deskew_applied: bool = False
    detected_angle: Optional[float] = None
    processed_image: Any = field(default=None, repr=False, compare=False)
    saved_to: Optional[str] = None

    @property
    def word_count(self) -> int:
        """Number of accepted words (FR-258 boxed summary)."""
        return len(self.words)

    @property
    def character_count(self) -> int:
        """Number of characters in the accepted text (FR-258 boxed summary)."""
        return len(self.text)

    @property
    def is_error(self) -> bool:
        """True when this run ended in the ``error`` status (FR-257)."""
        return self.status == STATUS_ERROR

    def render_status(self) -> str:
        """Return the human-readable status label for display (FR-257)."""
        return STATUS_LABELS.get(self.status, self.status)


def format_confidence(value: Optional[float]) -> str:
    """Render a normalised confidence as a whole-number percentage (FR-258).

    Args:
        value: A confidence in ``0.0-1.0``, or ``None`` when no usable value
            exists.

    Returns:
        ``"82%"`` style text, or ``"N/A"`` for ``None``/non-finite values so
        no NaN/infinite value ever reaches the display.

    Reference: SPEC.md Part IV — FR-256, FR-258.
    """
    if value is None:
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if number != number or number in (float("inf"), float("-inf")):  # NaN/inf guard
        return "N/A"
    return f"{int(round(number * 100))}%"


def confidence_range_text(words: Tuple[Word, ...]) -> str:
    """Render the min-max confidence range of a word set (FR-258 summary).

    Args:
        words: A tuple of :class:`Word` objects (accepted or low-confidence).

    Returns:
        ``"82%-95%"`` when at least two usable confidences exist, ``"82%"``
        for a single usable confidence, otherwise ``"N/A"``.

    Reference: SPEC.md Part IV — FR-258 (boxed confidence range).
    """
    usable = [word.confidence for word in words if word.confidence is not None]
    usable = [c for c in usable if c == c and c not in (float("inf"), float("-inf"))]
    if not usable:
        return "N/A"
    low = min(usable)
    high = max(usable)
    if len(usable) == 1:
        return format_confidence(low)
    return f"{format_confidence(low)}-{format_confidence(high)}"
