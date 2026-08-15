"""Tesseract OCR engine wrapper — PSM modes and per-word confidence (FR-254, FR-255).

Wraps ``pytesseract.image_to_data``: selects one of the four supported page
segmentation modes (``3``, ``6``, ``7``, ``11``; default ``6`` per
``rec_psm`` — FR-254), extracts per-word text / confidence / bounding box into
ordered :class:`Word` objects (FR-256 input), and returns them together with
the full extracted text in a frozen :class:`OcrOutput`.

Graceful degradation (FR-255):
    - ``pytesseract`` not installed → :class:`DependencyUnavailableError` with
      the exact install command.
    - Tesseract binary not on ``PATH`` → :class:`OcrError` with actionable
      install guidance (never a traceback).
    - ``image_to_data`` failing at runtime → :class:`OcrError` with a friendly
      message.

Tesseract is invoked only on the preprocessed (binary) image (FR-253, FR-254).
Everything runs locally — no network I/O (FR-261). ``cv2``/``pytesseract`` are
imported lazily (FR-250), so importing this module performs no OCR.

Reference: SPEC.md Part IV — Category T4 (FR-254-FR-255).
"""

import logging
from dataclasses import dataclass
from typing import Tuple

from decodebot.recognition.dependencies import import_optional
from decodebot.recognition.errors import OcrError, UnsupportedPsmError
from decodebot.recognition.result import Word

logger = logging.getLogger(__name__)

SUPPORTED_PSM_MODES: tuple[int, ...] = (3, 6, 7, 11)
"""The only page-segmentation modes allowed (FR-254)."""

DEFAULT_PSM: int = 6
"""Default page-segmentation mode (FR-254, FR-251 ``rec_psm`` default)."""

UNUSABLE_CONFIDENCE: float = -1.0
"""Tesseract's sentinel for "no usable confidence" — mapped to ``None``."""

TESSERACT_INSTALL_HINT = (
    "Tesseract OCR is not installed or not on PATH. Install it from "
    "https://github.com/tesseract-ocr/tesseract and ensure the 'tesseract' "
    "command is available, then try again."
)
"""Actionable guidance when the external Tesseract binary is missing (FR-255)."""


@dataclass(frozen=True)
class OcrOutput:
    """Words plus the full text produced by one Tesseract run (FR-254).

    Attributes:
        words: Per-word :class:`Word` objects in stable reading order
            (sorted by block/line/x position). Word text is non-empty.
        full_text: The full extracted text (words joined by spaces).
        psm: The page-segmentation mode used for this run.

    Reference: SPEC.md Part IV — FR-254.
    """

    words: Tuple[Word, ...]
    full_text: str
    psm: int


def _load_pytesseract():
    """Lazily import and return the ``pytesseract`` module (FR-250, FR-255).

    Kept as a tiny indirection so tests can inject a deterministic fake.
    """
    return import_optional("pytesseract")


def validate_psm(psm) -> int:
    """Validate a requested page-segmentation mode (FR-254).

    Args:
        psm: The requested PSM (int, or a ``str``/``float`` convertible to a
            supported mode).

    Returns:
        The validated integer PSM.

    Raises:
        UnsupportedPsmError: When the mode is not one of ``3``, ``6``, ``7``
            or ``11``.

    Reference: SPEC.md Part IV — FR-254 (PSM 3/6/7/11 only).
    """
    try:
        value = int(psm)
    except (TypeError, ValueError):
        raise UnsupportedPsmError(
            f"Unsupported PSM {psm!r}. Supported page-segmentation modes: "
            f"{', '.join(str(m) for m in SUPPORTED_PSM_MODES)}."
        ) from None
    if value not in SUPPORTED_PSM_MODES:
        raise UnsupportedPsmError(
            f"Unsupported PSM {value}. Supported page-segmentation modes: "
            f"{', '.join(str(m) for m in SUPPORTED_PSM_MODES)}."
        )
    return value


def ensure_tesseract_available() -> None:
    """Verify the external Tesseract binary is reachable (FR-255).

    Runs ``pytesseract.get_tesseract_version()`` — a pure local version probe.
    Raises :class:`OcrError` with install guidance when the binary is missing,
    so callers can degrade gracefully instead of crashing mid-OCR.

    Reference: SPEC.md Part IV — FR-255.
    """
    pytesseract = _load_pytesseract()
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:  # TesseractNotFoundError, OSError, etc.
        raise OcrError(TESSERACT_INSTALL_HINT) from exc


def _row(data: dict, key: str, index: int, default):
    """Index into an ``image_to_data`` column, falling back when absent."""
    values = data.get(key) or []
    if 0 <= index < len(values):
        return values[index]
    return default


def _extract_words(data: dict, psm: int) -> Tuple[Word, ...]:
    """Collect per-word rows (level 5) into ordered :class:`Word` objects.

    Args:
        data: The ``image_to_data`` dict-of-lists result.
        psm: The PSM used (recorded on each word's ordering context).

    Returns:
        Words in stable reading order. Blank text rows and non-word rows are
        skipped; rows with the ``-1`` confidence sentinel map to ``None`` and
        rows with invalid geometry get an empty bounding box.
    """
    texts = data.get("text") or []
    rows = []
    for index in range(len(texts)):
        if _row(data, "level", index, 0) != 5:
            continue
        text = str(texts[index] or "").strip()
        if not text:
            continue
        raw_conf = _row(data, "conf", index, UNUSABLE_CONFIDENCE)
        confidence = None if raw_conf < 0 else round(float(raw_conf) / 100.0, 4)
        left = _row(data, "left", index, -1)
        top = _row(data, "top", index, -1)
        width = _row(data, "width", index, -1)
        height = _row(data, "height", index, -1)
        geometry = (left, top, width, height)
        has_geometry = all(value >= 0 for value in geometry)
        bbox = tuple(int(value) for value in geometry) if has_geometry else ()
        block = _row(data, "block_num", index, 0)
        line = _row(data, "line_num", index, 0)
        rows.append((block, line, left, index, text, confidence, bbox))
    ordered = sorted(rows, key=lambda row: (row[0], row[1], row[2], row[3]))
    return tuple(
        Word(
            text=text,
            confidence=confidence,
            bbox=bbox,
            order=order,
            block=block,
            line=line,
        )
        for order, (block, line, left, _, text, confidence, bbox) in enumerate(ordered)
    )


def run_ocr(image, psm: int = DEFAULT_PSM) -> OcrOutput:
    """Run Tesseract on a preprocessed binary image (FR-254, FR-255).

    Args:
        image: The preprocessed single-channel binary image (FR-253 output).
        psm: One of ``3``, ``6``, ``7``, ``11`` (default ``6``).

    Returns:
        An :class:`OcrOutput` with ordered words and the full text.

    Raises:
        UnsupportedPsmError: When ``psm`` is outside the supported set.
        DependencyUnavailableError: When ``pytesseract`` is not installed.
        OcrError: When the Tesseract binary is missing or ``image_to_data``
            fails — both with friendly, actionable messages (FR-255).

    Reference: SPEC.md Part IV — Category T4 (FR-254-FR-255).
    """
    validated_psm = validate_psm(psm)
    pytesseract = _load_pytesseract()
    ensure_tesseract_available()
    config = f"--psm {validated_psm}"
    try:
        data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
    except OcrError:
        raise
    except Exception as exc:
        logger.warning("Tesseract image_to_data failed: %s", exc)
        raise OcrError(
            "Tesseract could not read this image. Please ensure it is a valid "
            "PNG/JPEG with text content."
        ) from exc

    words = _extract_words(data, validated_psm)
    full_text = " ".join(word.text for word in words)
    logger.info(
        "OCR run complete: psm=%d, %d words, %d characters.",
        validated_psm,
        len(words),
        len(full_text),
    )
    return OcrOutput(words=words, full_text=full_text, psm=validated_psm)
