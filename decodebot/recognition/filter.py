"""Confidence filtering, status classification and result assembly (FR-256-FR-258).

Given the ordered words from :mod:`decodebot.recognition.ocr_engine`, this
module applies the confidence threshold (default 80%, FR-256), routes
below-threshold words to ``low_confidence_words``, excludes unusable words
(empty text / empty bounding box / no usable confidence) from acceptance,
derives exactly one FR-257 status, and assembles the finalized
:class:`RecognitionResult` (FR-258).

Status contract (FR-257):
    - ``accepted``      — at least one word passed the threshold.
    - ``low_confidence``— words were detected but none passed the threshold.
    - ``no_text``       — no words were detected at all.
    - ``error``         — any failure path (assembled via :func:`error_result`).

Aggregation (documented engine decision): the ``overall_confidence`` is the
arithmetic mean of the accepted words' confidences, or ``None`` when no word
was accepted. Invalid/sentinel confidences (``None``) never count toward
either the accepted or the low-confidence lists (FR-256).

Reference: SPEC.md Part IV — Categories T5-T6 (FR-256-FR-258).
"""

from __future__ import annotations

from typing import Optional, Tuple

from decodebot.recognition.ocr_engine import DEFAULT_PSM
from decodebot.recognition.result import (
    STATUS_ACCEPTED,
    STATUS_LOW_CONFIDENCE,
    STATUS_NO_TEXT,
    RecognitionResult,
    Word,
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.80
"""Default minimum accepted per-word confidence (FR-256, FR-251)."""

_STATUS_MESSAGES = {
    STATUS_ACCEPTED: "Text recognized with high confidence.",
    STATUS_LOW_CONFIDENCE: "Text detected, but confidence was below the threshold.",
    STATUS_NO_TEXT: "No text detected in this image.",
}


def filter_words(
    words: Tuple[Word, ...],
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> Tuple[Tuple[Word, ...], Tuple[Word, ...]]:
    """Split words into ``(accepted, low_confidence)`` (FR-256).

    A word is accepted when it has non-empty text, a non-empty bounding box,
    a usable confidence (not ``None`` and within ``0-1``) and a confidence >=
    ``threshold``. Words with confidence below the threshold are routed to the
    low-confidence list. Unusable words (empty text, empty bounding box, or
    ``None``/out-of-range confidence) are excluded entirely — they appear in
    neither list (FR-256). The Tesseract ``-1`` sentinel is mapped to ``None``
    by the OCR engine, but out-of-range confidences are also treated as
    unusable here for robustness.

    Args:
        words: Ordered :class:`Word` objects from the OCR engine.
        threshold: Minimum confidence (0-1) for acceptance (default 0.80).

    Returns:
        ``(accepted, low_confidence)`` tuples, each preserving reading order.

    Reference: SPEC.md Part IV — FR-256.
    """
    accepted = []
    low_confidence = []
    for word in words:
        if not word.text or not word.bbox:
            continue
        confidence = word.confidence
        if confidence is None or confidence < 0 or confidence > 1:
            continue
        if confidence >= threshold:
            accepted.append(word)
        else:
            low_confidence.append(word)
    return tuple(accepted), tuple(low_confidence)


def classify_status(
    accepted: Tuple[Word, ...],
    low_confidence: Tuple[Word, ...],
) -> str:
    """Derive the single FR-257 status from the filtered word lists.

    Args:
        accepted: Words that passed the confidence threshold.
        low_confidence: Words that existed but stayed below the threshold.

    Returns:
        One of ``accepted`` / ``low_confidence`` / ``no_text`` (FR-257).

    Reference: SPEC.md Part IV — FR-257.
    """
    if accepted:
        return STATUS_ACCEPTED
    if low_confidence:
        return STATUS_LOW_CONFIDENCE
    return STATUS_NO_TEXT


def aggregate_confidence(accepted: Tuple[Word, ...]) -> Optional[float]:
    """Arithmetic mean of the accepted words' confidence (0-1).

    Args:
        accepted: The accepted :class:`Word` objects.

    Returns:
        The mean confidence, or ``None`` when no word was accepted.
    """
    usable = [word.confidence for word in accepted if word.confidence is not None]
    if not usable:
        return None
    return round(sum(usable) / len(usable), 4)


def build_result(
    words: Tuple[Word, ...],
    full_text: str = "",
    image_path: str = "",
    psm: int = DEFAULT_PSM,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    duration_ms: float = 0.0,
    deskew_applied: bool = False,
    detected_angle: Optional[float] = None,
    processed_image: object = None,
    message: Optional[str] = None,
) -> RecognitionResult:
    """Assemble the finalized :class:`RecognitionResult` (FR-258).

    Runs filtering and status classification over the OCR words and fills the
    structured result with the FR-258 fields: ``status``, ``text`` (filtered),
    ``full_text`` (pre-filter), ``words``/``low_confidence_words``,
    ``overall_confidence``, ``image_path``, ``psm`` and ``duration_ms``.

    Args:
        words: Ordered words from the OCR engine.
        full_text: The pre-filter full text (informational).
        image_path: The local image processed (never modified).
        psm: The page-segmentation mode used.
        confidence_threshold: The threshold applied (default 0.80).
        duration_ms: Wall-clock duration of the run.
        deskew_applied: Whether preprocessing corrected skew.
        detected_angle: The estimated skew in degrees (if any).
        processed_image: Opaque reference to the preprocessed image (binary).
        message: Optional override for the status message.

    Returns:
        A frozen :class:`RecognitionResult` with exactly one FR-257 status.

    Reference: SPEC.md Part IV — FR-256, FR-257, FR-258.
    """
    accepted, low_confidence = filter_words(words, confidence_threshold)
    status = classify_status(accepted, low_confidence)
    if message is None:
        message = _STATUS_MESSAGES.get(status, status)
    return RecognitionResult(
        status=status,
        text=" ".join(word.text for word in accepted),
        full_text=full_text,
        words=accepted,
        low_confidence_words=low_confidence,
        overall_confidence=aggregate_confidence(accepted),
        image_path=image_path,
        psm=psm,
        confidence_threshold=confidence_threshold,
        duration_ms=duration_ms,
        message=message,
        deskew_applied=deskew_applied,
        detected_angle=detected_angle,
        processed_image=processed_image,
    )


def error_result(
    message: str,
    image_path: str = "",
    psm: int = DEFAULT_PSM,
    duration_ms: float = 0.0,
) -> RecognitionResult:
    """Assemble an ``error``-status result for a failure path (FR-257).

    Args:
        message: The friendly, actionable error message (FR-255).
        image_path: The image being processed (if known).
        psm: The page-segmentation mode requested.
        duration_ms: Elapsed time before the failure (if measured).

    Returns:
        A frozen :class:`RecognitionResult` with status ``error``.

    Reference: SPEC.md Part IV — FR-257 (``error`` status), FR-255.
    """
    return RecognitionResult(
        status="error",
        image_path=image_path,
        psm=psm,
        duration_ms=duration_ms,
        message=message,
    )
