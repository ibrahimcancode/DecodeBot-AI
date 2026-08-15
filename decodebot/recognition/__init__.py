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
    OutputError,
    RecognitionError,
    UnsupportedImageError,
    UnsupportedPsmError,
)
from decodebot.recognition.filter import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    aggregate_confidence,
    build_result,
    classify_status,
    error_result,
    filter_words,
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
from decodebot.recognition.ocr_engine import (
    DEFAULT_PSM,
    SUPPORTED_PSM_MODES,
    OcrOutput,
    ensure_tesseract_available,
    run_ocr,
    validate_psm,
)
from decodebot.recognition.result import (
    ALL_STATUSES,
    STATUS_ACCEPTED,
    STATUS_ERROR,
    STATUS_LOW_CONFIDENCE,
    STATUS_NO_TEXT,
    DEFAULT_OUTPUT_DIR,
    RecognitionResult,
    Word,
    confidence_range_text,
    format_confidence,
    save_text_output,
)

__all__ = [
    "ALL_STATUSES",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "DEFAULT_MAX_DIMENSION",
    "DEFAULT_MAX_FILE_MB",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PSM",
    "DependencyUnavailableError",
    "ImageLoadError",
    "ImageValidationError",
    "IngestedImage",
    "OcrError",
    "OcrOutput",
    "OutputError",
    "RecognitionError",
    "RecognitionResult",
    "STATUS_ACCEPTED",
    "STATUS_ERROR",
    "STATUS_LOW_CONFIDENCE",
    "STATUS_NO_TEXT",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_FORMATS_TEXT",
    "SUPPORTED_PSM_MODES",
    "UnsupportedImageError",
    "UnsupportedPsmError",
    "Word",
    "aggregate_confidence",
    "build_result",
    "check_dimensions",
    "check_extension",
    "check_file_size",
    "classify_status",
    "confidence_range_text",
    "decode_image",
    "ensure_tesseract_available",
    "error_result",
    "filter_words",
    "format_confidence",
    "ingest_image",
    "run_ocr",
    "save_text_output",
    "validate_path",
    "validate_psm",
]
