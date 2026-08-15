"""Image ingestion — existence, format, size and dimension bounds (FR-252).

Validates the local image path (exists, regular file, PNG/JPG/JPEG extension
case-insensitively), enforces the configurable file-size limit *before*
decoding oversized content (FR-252, NFR-093), decodes the pixels through
OpenCV's ``imdecode`` (lazy import), validates the decoded content rather than
the extension alone, enforces the longest-edge dimension limit, and returns an
immutable :class:`IngestedImage` carrying the decoded array plus metadata.
The original file is never modified and no output file is created (FR-261).

Decode robustness:
    - The bytes are read with ``numpy.fromfile`` and decoded with
      ``cv2.imdecode`` so non-ASCII Windows paths decode correctly.
    - Content is authoritative: ``imdecode`` sniffs the real format from the
      bytes. A PNG-named file holding valid JPEG bytes still decodes; bytes
      that decode to ``None`` (corrupt, empty, or unsupported content) are
      reported as undecodable with a friendly error (FR-252 edge case).

Reference: SPEC.md Part IV — Category T2 (FR-252), NFR-093.
"""

import logging
import pathlib
from dataclasses import dataclass, field
from typing import Union

from decodebot.recognition.dependencies import import_optional
from decodebot.recognition.errors import (
    ImageLoadError,
    ImageValidationError,
    UnsupportedImageError,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset = frozenset({".png", ".jpg", ".jpeg"})
"""Case-insensitive supported extensions (PNG, JPG and JPEG — FR-252)."""

SUPPORTED_FORMATS_TEXT = "PNG, JPG and JPEG"
"""Human-readable list used in friendly error messages (FR-252)."""

DEFAULT_MAX_FILE_MB = 10
"""Default maximum input file size in MB (FR-252, NFR-093)."""

DEFAULT_MAX_DIMENSION = 4096
"""Default maximum longest-edge dimension in pixels (FR-252, NFR-093)."""


@dataclass(frozen=True)
class IngestedImage:
    """An image that passed all ingestion validation (FR-252).

    Attributes:
        path: The local file path as provided (never modified).
        format: Normalised format label from the extension (``PNG``/``JPG``/
            ``JPEG``) — informative only; decode validity comes from content.
        width, height: Decoded pixel dimensions.
        size_bytes: File size on disk.
        image: The decoded OpenCV image (BGR, ``numpy`` array). Excluded from
            equality/repr because arrays are opaque and comparison is costly.

    Reference: SPEC.md Part IV — FR-252.
    """

    path: str
    format: str
    width: int
    height: int
    size_bytes: int
    image: object = field(repr=False, compare=False)


def _display_name(path: pathlib.Path) -> str:
    """Return a friendly basename — never the full local path (FR-261)."""
    return path.name


def _as_path(path: Union[str, pathlib.Path]) -> pathlib.Path:
    return pathlib.Path(path)


def validate_path(path: Union[str, pathlib.Path]) -> pathlib.Path:
    """Verify the path exists and points to a regular file (FR-252).

    Args:
        path: A ``pathlib``-compatible local image path.

    Returns:
        The resolved :class:`pathlib.Path`.

    Raises:
        ImageLoadError: When the path does not exist.
        ImageValidationError: When the path is not a regular file (e.g. a
            directory).

    Reference: SPEC.md Part IV — FR-252 (missing file → friendly error).
    """
    resolved = _as_path(path)
    if not resolved.exists():
        raise ImageLoadError(f"Image file not found: {_display_name(resolved)}")
    if not resolved.is_file():
        raise ImageValidationError(f"Not a regular image file: {_display_name(resolved)}")
    return resolved


def check_extension(path: pathlib.Path) -> str:
    """Validate the file extension case-insensitively (FR-252).

    Args:
        path: The validated local file path.

    Returns:
        The lowercased extension (e.g. ``".png"``).

    Raises:
        UnsupportedImageError: When the extension is outside PNG/JPG/JPEG.

    Reference: SPEC.md Part IV — FR-252 (supported formats).
    """
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedImageError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported formats: {SUPPORTED_FORMATS_TEXT}."
        )
    return extension


def check_file_size(
    path: pathlib.Path, max_file_mb: Union[int, float] = DEFAULT_MAX_FILE_MB
) -> int:
    """Enforce the file-size limit before any decode (FR-252, NFR-093).

    Args:
        path: The validated local file path.
        max_file_mb: Maximum allowed size in MB (default 10).

    Returns:
        The file size in bytes.

    Raises:
        ImageValidationError: When the file exceeds the configured limit;
            oversized files are never fully loaded into memory.

    Reference: SPEC.md Part IV — FR-252, NFR-093.
    """
    size = path.stat().st_size
    max_bytes = max(1, int(max_file_mb * 1024 * 1024))
    if size > max_bytes:
        if max_bytes >= 1024 * 1024 and max_bytes % (1024 * 1024) == 0:
            limit_label = f"{max_bytes // (1024 * 1024)} MB"
        else:
            limit_label = f"{max_bytes}-byte"
        raise ImageValidationError(
            f"Image too large: {_display_name(path)} is {size / (1024 * 1024):.1f} MB, "
            f"over the {limit_label} limit."
        )
    return size


def _load_cv2():
    """Lazily import and return the ``cv2`` module (FR-250).

    Kept as a tiny indirection so tests can inject a deterministic decoder
    without a real OpenCV install (FR-262) — same pattern as
    ``decodebot.recommender.ranker._import_cosine_similarity``.
    """
    return import_optional("cv2")


def _load_numpy():
    """Lazily import and return the ``numpy`` module (FR-250)."""
    return import_optional("numpy")


def decode_image(path: pathlib.Path):
    """Decode the image bytes via OpenCV (lazy import) (FR-252).

    Args:
        path: The validated local file path.

    Returns:
        The decoded OpenCV image (BGR, ``numpy`` array).

    Raises:
        ImageLoadError: When the bytes are corrupt, empty, or decode to no
            image at all — detected from content, not the extension.

    Reference: SPEC.md Part IV — FR-252 (corrupt/undecodable → friendly error).
    """
    cv2 = _load_cv2()
    np = _load_numpy()
    buffer = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(
            f"Could not decode image (corrupt, empty, or unsupported content): "
            f"{_display_name(path)}"
        )
    return image


def check_dimensions(
    image, max_dimension: Union[int, float] = DEFAULT_MAX_DIMENSION
) -> tuple[int, int]:
    """Enforce the longest-edge dimension limit after decode (FR-252, NFR-093).

    Args:
        image: The decoded OpenCV image.
        max_dimension: Maximum longest-edge length in pixels (default 4096).

    Returns:
        ``(width, height)`` of the decoded image.

    Raises:
        ImageValidationError: When the longest edge exceeds the limit.

    Reference: SPEC.md Part IV — FR-252, NFR-093.
    """
    height, width = image.shape[:2]
    longest = max(height, width)
    limit = max(1, int(max_dimension))
    if longest > limit:
        raise ImageValidationError(
            f"Image too large: longest edge is {longest}px, " f"over the {limit}px limit."
        )
    return width, height


def ingest_image(
    path: Union[str, pathlib.Path],
    max_file_mb: Union[int, float] = DEFAULT_MAX_FILE_MB,
    max_dimension: Union[int, float] = DEFAULT_MAX_DIMENSION,
) -> IngestedImage:
    """Validate and decode a local image (single ingestion entry point).

    Args:
        path: A ``pathlib``-compatible local image path.
        max_file_mb: Maximum input file size in MB (default 10).
        max_dimension: Maximum longest-edge dimension in pixels (default 4096).

    Returns:
        An immutable :class:`IngestedImage` with the decoded pixels and
        metadata. The original file is left byte-for-byte unchanged and no
        output file is created.

    Raises:
        ImageLoadError: Missing/unreadable/corrupt image.
        ImageValidationError: Directory path, size or dimension bound breach.
        UnsupportedImageError: Unsupported extension.

    Reference: SPEC.md Part IV — Category T2 (FR-252).
    """
    resolved = validate_path(path)
    extension = check_extension(resolved)
    size_bytes = check_file_size(resolved, max_file_mb)
    image = decode_image(resolved)
    width, height = check_dimensions(image, max_dimension)

    logger.info(
        "Ingested image %s (%s, %dx%d, %d bytes).",
        _display_name(resolved),
        extension,
        width,
        height,
        size_bytes,
    )
    return IngestedImage(
        path=str(resolved),
        format=extension[1:].upper(),
        width=width,
        height=height,
        size_bytes=size_bytes,
        image=image,
    )
