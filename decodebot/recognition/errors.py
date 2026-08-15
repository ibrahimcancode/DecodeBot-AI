"""Domain exception hierarchy for the OCR Recognition Engine (FR-252, FR-255).

Every failure path in the engine surfaces as one of these structured types so
the CLI, the GUI and the automated tests can branch on error *kind* without
string-matching. Messages are written for a human user: actionable, friendly
and never a raw traceback (FR-255). They also never disclose the full
absolute local path when a shorter, friendlier name is enough (FR-261,
"actionable errors without unnecessary local-path disclosure").

Reference: SPEC.md Part IV — Categories T1-T8 (FR-249-FR-262).
"""


class RecognitionError(Exception):
    """Base class for every OCR Recognition Engine error (FR-255)."""


class ImageLoadError(RecognitionError):
    """The image could not be located or its bytes could not be decoded."""


class ImageValidationError(RecognitionError):
    """The image failed a validation rule (file size, dimensions, content)."""


class UnsupportedImageError(ImageValidationError):
    """The file extension is not in the supported set (PNG, JPG, JPEG)."""


class DependencyUnavailableError(RecognitionError):
    """An optional dependency (cv2 / pytesseract / Tesseract) is missing."""


class OcrError(RecognitionError):
    """Tesseract ran but failed to produce usable output (FR-254)."""


class UnsupportedPsmError(RecognitionError):
    """A page-segmentation mode outside {3, 6, 7, 11} was requested (FR-254)."""
