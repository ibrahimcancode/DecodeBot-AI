"""FR-253 preprocessing pipeline: grayscale → Gaussian blur → deskew → adaptive threshold.

Each stage is a separate, testable function so a stage can be skipped or fixed
independently (FR-253), and the pipeline runs headless via
``opencv-python-headless`` (never touches a GUI / display). The whole chain is
implemented with numpy/OpenCV arrays only; no image is ever written to disk by
this module (FR-261).

Pipeline contract (FR-253, FR-256):
    - Input:  a decoded OpenCV image (BGR or already single-channel).
    - Output: a single-channel binary image (pixel values exactly ``0`` or
      ``255``) with dark text on a white background — the polarity Tesseract
      expects natively.
    - ``deskew`` returns ``(image, angle, applied)``: the corrected image, the
      estimated skew in degrees, and whether a correction was actually applied
      (estimated skew beyond ~0.5°, FR-253). ``detected_angle``/``applied``
      are surfaced on the ``RecognitionResult``.
    - Blank (all-black or all-white) images run the whole pipeline without
      crashing (FR-253 edge case); downstream OCR then reports ``no_text``
      (FR-257).

Reference: SPEC.md Part IV — Category T3 (FR-253), NFR-093.
"""

import logging
from typing import Tuple

from decodebot.recognition.dependencies import import_optional

logger = logging.getLogger(__name__)

DESKEW_THRESHOLD_DEG = 0.5
"""Estimated skew below this magnitude (in degrees) is left uncorrected (FR-253)."""

DEFAULT_BLUR_KERNEL = 5
"""Default 5x5 Gaussian kernel (FR-253)."""

DEFAULT_BLOCK_SIZE = 35
DEFAULT_C = 10
"""Defaults for the Gaussian adaptive-threshold window/offset (FR-253)."""

MAX_ANGLE_DEG = 45.0
"""Angle normalization range bound; anything beyond ±45° maps into range."""


def _load_cv2():
    """Lazily import and return the ``cv2`` module (FR-250)."""
    return import_optional("cv2")


def _load_numpy():
    """Lazily import and return the ``numpy`` module (FR-250)."""
    return import_optional("numpy")


def to_grayscale(image):
    """Convert a BGR image to a single-channel grayscale image (FR-253 step 1).

    Args:
        image: A decoded OpenCV image (BGR) or an already single-channel image.

    Returns:
        A single-channel ``uint8`` array.

    Reference: SPEC.md Part IV — FR-253 (stage 1).
    """
    cv2 = _load_cv2()
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def blur(
    image,
    kernel_size: int = DEFAULT_BLUR_KERNEL,
    sigma: float = 0.0,
):
    """Apply a Gaussian blur (FR-253 step 2).

    Args:
        image: A single-channel grayscale image.
        kernel_size: Odd kernel side length (even values are bumped up by one
            so OpenCV accepts them).
        sigma: Gaussian sigma; ``0.0`` asks OpenCV to derive it from the
            kernel size.

    Returns:
        The blurred single-channel image (same shape and dtype).

    Reference: SPEC.md Part IV — FR-253 (stage 2).
    """
    cv2 = _load_cv2()
    kernel = int(kernel_size)
    if kernel % 2 == 0:
        kernel += 1
    if kernel < 3:
        kernel = 3
    return cv2.GaussianBlur(image, (kernel, kernel), float(sigma))


def normalize_angle(angle: float) -> float:
    """Map a ``cv2.minAreaRect`` angle (in ``[-90, 0)``) into ``[-45, 45]``.

    Args:
        angle: An angle in degrees as returned by ``cv2.minAreaRect``.

    Returns:
        The equivalent angle in ``[-45, 45]`` degrees.

    Reference: SPEC.md Part IV — FR-253 (deskew stage).
    """
    if angle < -MAX_ANGLE_DEG:
        return 90.0 + angle
    return angle


def should_deskew(angle: float, threshold: float = DESKEW_THRESHOLD_DEG) -> bool:
    """Decide whether an estimated skew warrants correction (FR-253).

    Args:
        angle: The estimated skew in degrees.
        threshold: Minimum |angle| (default 0.5°) that triggers correction.

    Returns:
        True when the absolute angle exceeds the threshold.

    Reference: SPEC.md Part IV — FR-253 (skew applied only when > ~0.5°).
    """
    return abs(angle) > threshold


def estimate_skew(image) -> float:
    """Estimate the text skew angle in degrees (FR-253 stage 3, pure estimator).

    Binarises the grayscale image with OTSU (inverted so text is bright),
    collects the non-zero pixel coordinates and fits the minimum-area
    bounding rectangle; its orientation (normalized to ``[-45, 45]``) is the
    skew estimate. Blank images yield ``0.0``.

    Args:
        image: A single-channel grayscale image.

    Returns:
        The estimated skew in degrees, normalized to ``[-45, 45]``, ``0.0``
        when there is no text-like content to measure.

    Reference: SPEC.md Part IV — FR-253 (automatic skew estimation).
    """
    cv2 = _load_cv2()
    np = _load_numpy()
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binary > 0))
    if coords.size == 0:
        return 0.0
    coords = coords[:, ::-1].astype(np.float32)  # (y, x) -> (x, y)
    angle = cv2.minAreaRect(coords)[-1]
    return normalize_angle(float(angle))


def deskew(image):
    """Correct the image skew when it exceeds ~0.5° (FR-253 stage 3).

    Args:
        image: A single-channel grayscale image.

    Returns:
        ``(rotated, angle, applied)``: the deskewed image (dimensions
        preserved), the estimated skew in degrees, and whether a rotation was
        actually applied.

    Reference: SPEC.md Part IV — FR-253 (automatic skew correction).
    """
    cv2 = _load_cv2()
    angle = estimate_skew(image)
    if not should_deskew(angle):
        return image, angle, False
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    logger.info("Deskewed image by %.2f degrees.", angle)
    return rotated, angle, True


def threshold(
    image,
    block_size: int = DEFAULT_BLOCK_SIZE,
    c: float = DEFAULT_C,
    max_value: int = 255,
):
    """Apply Gaussian adaptive thresholding → binary 0/255 (FR-253 stage 4).

    Uses ``THRESH_BINARY`` polarity: dark text becomes black (0) on a white
    (255) background — the polarity Tesseract expects natively.

    Args:
        image: A single-channel grayscale image.
        block_size: Odd local-window side length (even values bumped up).
        c: Constant subtracted from the locally computed mean.
        max_value: Brightness of the foreground (default 255).

    Returns:
        A binary single-channel image whose pixel values are exactly
        ``{0, max_value}``.

    Reference: SPEC.md Part IV — FR-253 (stage 4).
    """
    cv2 = _load_cv2()
    block = int(block_size)
    if block % 2 == 0:
        block += 1
    if block < 3:
        block = 3
    return cv2.adaptiveThreshold(
        image,
        int(max_value),
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block,
        float(c),
    )


def preprocess_image(
    image,
    blur_kernel_size: int = DEFAULT_BLUR_KERNEL,
    blur_sigma: float = 0.0,
    block_size: int = DEFAULT_BLOCK_SIZE,
    c: float = DEFAULT_C,
) -> Tuple:
    """Run the full fixed FR-253 pipeline and return the binary image + metadata.

    Args:
        image: A decoded OpenCV image (BGR or single-channel).
        blur_kernel_size: Gaussian kernel side (default 5).
        blur_sigma: Gaussian sigma (default derived by OpenCV).
        block_size: Adaptive-threshold window (default 35).
        c: Adaptive-threshold offset (default 10).

    Returns:
        ``(binary, metadata)`` where ``binary`` is the single-channel 0/255
        image ready for Tesseract and ``metadata`` is a dict with
        ``deskew_applied`` (bool) and ``detected_angle`` (float) for the
        ``RecognitionResult``.

    Reference: SPEC.md Part IV — FR-253, FR-256 (input to Tesseract).
    """
    gray = to_grayscale(image)
    blurred = blur(gray, blur_kernel_size, blur_sigma)
    deskewed, angle, applied = deskew(blurred)
    binary = threshold(deskewed, block_size, c)
    metadata = {"deskew_applied": applied, "detected_angle": angle}
    return binary, metadata
