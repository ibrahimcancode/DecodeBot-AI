"""DecodeBot OCR Recognition Engine — Wave 4 package (FR-249, FR-250).

This package implements the optional OCR Image/Text Recognition Engine:
ingestion (``ingestor``), the grayscale → Gaussian blur → deskew → adaptive
threshold preprocessing pipeline (``preprocess``), the Tesseract wrapper with
PSM modes (``ocr_engine``), confidence filtering (``filter``), and the
structured result model (``result``). The thin CLI/GUI bootstrap lives in
``app_recognition`` (W4-M5).

Isolation guarantees (FR-249, FR-250 — enforced by ``tests/test_wave4_isolation.py``):
    - ``opencv-python-headless`` (``cv2``) and ``pytesseract`` are *optional*
      dependencies, imported lazily — never at module scope — behind the
      helper in :mod:`decodebot.recognition.dependencies`.
    - No module in ``decodebot/core/``, ``decodebot/rules/`` or
      ``decodebot/gui/`` imports this package, ``cv2`` or ``pytesseract``,
      except the thin wiring files (dispatcher, app_gui, app, main).
    - Merely importing this package performs no OCR, loads no image, and never
      touches the Tesseract binary or the network (FR-261).

Reference: SPEC.md Part IV — Categories T1-T8 (FR-249-FR-262).
"""

from decodebot.recognition.errors import (
    DependencyUnavailableError,
    ImageLoadError,
    ImageValidationError,
    OcrError,
    RecognitionError,
    UnsupportedImageError,
    UnsupportedPsmError,
)
from decodebot.recognition.ingestor import (
    DEFAULT_MAX_DIMENSION,
    DEFAULT_MAX_FILE_MB,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_FORMATS_TEXT,
    IngestedImage,
    check_dimensions,
    check_extension,
    check_file_size,
    decode_image,
    ingest_image,
    validate_path,
)
from decodebot.recognition.result import (
    ALL_STATUSES,
    STATUS_ACCEPTED,
    STATUS_ERROR,
    STATUS_LOW_CONFIDENCE,
    STATUS_NO_TEXT,
    RecognitionResult,
    Word,
    confidence_range_text,
    format_confidence,
)

__all__ = [
    "ALL_STATUSES",
    "DEFAULT_MAX_DIMENSION",
    "DEFAULT_MAX_FILE_MB",
    "DependencyUnavailableError",
    "ImageLoadError",
    "ImageValidationError",
    "IngestedImage",
    "OcrError",
    "RecognitionError",
    "RecognitionResult",
    "STATUS_ACCEPTED",
    "STATUS_ERROR",
    "STATUS_LOW_CONFIDENCE",
    "STATUS_NO_TEXT",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_FORMATS_TEXT",
    "UnsupportedImageError",
    "UnsupportedPsmError",
    "Word",
    "check_dimensions",
    "check_extension",
    "check_file_size",
    "confidence_range_text",
    "decode_image",
    "format_confidence",
    "ingest_image",
    "validate_path",
]
