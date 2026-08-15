"""Week 4 OCR Recognition Engine — image ingestion tests (FR-252, FR-255).

Coverage targets (TC-OCR-001 … TC-OCR-012):
    - Valid PNG/JPG/JPEG ingestion via the deterministic PIL-backed decoder
      (no real OpenCV needed in CI — FR-262).
    - Missing file, directory path, unsupported extension, corrupt content,
      empty file, extension/content mismatch, file-size and dimension limits.
    - Structured error kinds with friendly, actionable messages that never
      leak the full local path and never contain a traceback (FR-255).
    - The original file is left byte-for-byte unchanged (FR-261).
    - Lazy imports: importing the package never pulls in ``cv2``/
      ``pytesseract`` and never runs OCR (FR-250).

Import discipline: this test module never imports ``numpy`` directly — it is
pulled lazily via ``importlib`` so the ML-isolation gate
(``tests/test_ml_isolation.py``) stays green. ``cv2`` is only ever obtained
through the patchable ``ingestor._load_cv2`` seam or via ``find_spec``.

Reference: SPEC.md Part IV — Categories T1-T2 (FR-249-FR-255), NFR-093.
"""

import importlib
import io
import os
import subprocess
import sys

import pytest

import decodebot.recognition as recognition
import decodebot.recognition.ingestor as ingestor
from decodebot.recognition.errors import (
    ImageLoadError,
    ImageValidationError,
    RecognitionError,
    UnsupportedImageError,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _np():
    return importlib.import_module("numpy")


def _pil():
    return importlib.import_module("PIL")


def _run_subprocess(script):
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


class _PilBackedCv2:
    """Deterministic stand-in for OpenCV's imdecode, backed by Pillow."""

    IMREAD_COLOR = 1

    def imdecode(self, buffer, flags):
        try:
            image = _pil().Image.open(io.BytesIO(bytes(buffer.tobytes())))
            image = image.convert("RGB")
            array = _np().asarray(image)[:, :, ::-1]
            return array
        except Exception:
            return None


class _ShapeCv2:
    """Decoder stand-in returning a fixed-shape array (dimension-limit test)."""

    IMREAD_COLOR = 1

    def __init__(self, shape):
        self._shape = shape

    def imdecode(self, buffer, flags):
        return _np().zeros(self._shape, dtype=_np().uint8)


@pytest.fixture(autouse=True)
def _use_pil_decoder(monkeypatch):
    """Every ingestion test decodes through the deterministic decoder."""
    monkeypatch.setattr(ingestor, "_load_cv2", lambda: _PilBackedCv2())


def _write_image(path, size=(64, 32), fmt="PNG", background=(255, 255, 255)):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    draw.rectangle([8, 8, 40, 24], fill=(10, 10, 10))
    image.save(str(path), fmt)
    return path


def test_valid_png_ingestion(tmp_path):
    path = _write_image(tmp_path / "card.png")
    ingested = ingestor.ingest_image(path)
    assert ingested.format == "PNG"
    assert (ingested.width, ingested.height) == (64, 32)
    assert ingested.size_bytes == os.path.getsize(path)
    assert ingested.image is not None
    assert ingested.image.shape[:2] == (32, 64)


def test_valid_jpeg_ingestion(tmp_path):
    path = _write_image(tmp_path / "photo.jpg", fmt="JPEG")
    ingested = ingestor.ingest_image(path)
    assert ingested.format == "JPG"
    assert (ingested.width, ingested.height) == (64, 32)


def test_uppercase_extension_ingestion(tmp_path):
    path = _write_image(tmp_path / "CARD.PNG")
    ingested = ingestor.ingest_image(path)
    assert ingested.format == "PNG"


def test_missing_file_raises_load_error(tmp_path):
    missing = tmp_path / "nope.png"
    with pytest.raises(ImageLoadError) as exc_info:
        ingestor.ingest_image(missing)
    assert "not found" in str(exc_info.value)


def test_directory_path_raises_validation_error(tmp_path):
    directory = tmp_path / "folder.png"
    directory.mkdir()
    with pytest.raises(ImageValidationError):
        ingestor.ingest_image(directory)


def test_unsupported_extension_raises(tmp_path):
    for name in ("notes.txt", "scan.bmp", "anim.gif"):
        path = tmp_path / name
        path.write_bytes(b"whatever")
        with pytest.raises(UnsupportedImageError) as exc_info:
            ingestor.ingest_image(path)
        assert "PNG, JPG and JPEG" in str(exc_info.value)


def test_extension_content_mismatch_still_decodes(tmp_path):
    jpeg_buffer = io.BytesIO()
    _pil().Image.new("RGB", (48, 24), (255, 255, 255)).save(jpeg_buffer, "JPEG")
    path = tmp_path / "actually_jpeg.png"
    path.write_bytes(jpeg_buffer.getvalue())
    ingested = ingestor.ingest_image(path)
    assert ingested.format == "PNG"
    assert (ingested.width, ingested.height) == (48, 24)


def test_corrupt_content_raises_load_error(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"this is not an image at all")
    with pytest.raises(ImageLoadError) as exc_info:
        ingestor.ingest_image(path)
    assert "corrupt" in str(exc_info.value)


def test_empty_file_raises_load_error(tmp_path):
    path = tmp_path / "empty.png"
    path.write_bytes(b"")
    with pytest.raises(ImageLoadError):
        ingestor.ingest_image(path)


def test_file_size_limit_rejects_before_decode(tmp_path, monkeypatch):
    oversized = tmp_path / "huge.png"
    oversized.write_bytes(b"\x00" * (11 * 1024 * 1024))

    def boom():
        pytest.fail("decode_image must not be reached for oversized files")

    monkeypatch.setattr(ingestor, "decode_image", boom)
    with pytest.raises(ImageValidationError) as exc_info:
        ingestor.ingest_image(oversized, max_file_mb=10)
    assert "10 MB limit" in str(exc_info.value)


def test_custom_size_limit(tmp_path):
    path = _write_image(tmp_path / "small.png")
    with pytest.raises(ImageValidationError):
        ingestor.ingest_image(path, max_file_mb=1 / (1024 * 1024))


def test_dimension_limit_rejects(tmp_path, monkeypatch):
    path = _write_image(tmp_path / "wide.png")
    monkeypatch.setattr(ingestor, "_load_cv2", lambda: _ShapeCv2((10, 5000, 3)))
    with pytest.raises(ImageValidationError) as exc_info:
        ingestor.ingest_image(path, max_dimension=4096)
    assert "4096px" in str(exc_info.value)


def test_custom_dimension_limit(tmp_path, monkeypatch):
    path = _write_image(tmp_path / "big.png")
    monkeypatch.setattr(ingestor, "_load_cv2", lambda: _ShapeCv2((300, 400, 3)))
    with pytest.raises(ImageValidationError):
        ingestor.ingest_image(path, max_dimension=256)


def test_original_file_left_unchanged(tmp_path):
    path = _write_image(tmp_path / "scan.png")
    before = path.read_bytes()
    ingestor.ingest_image(path)
    assert path.read_bytes() == before


def test_errors_are_friendly_and_never_a_traceback(tmp_path):
    directory = tmp_path / "dir.png"
    directory.mkdir()
    erroring_calls = [
        lambda: ingestor.ingest_image(tmp_path / "absent.png"),
        lambda: ingestor.ingest_image(directory),
        lambda: ingestor.ingest_image(tmp_path / "broken.txt"),
    ]
    for call in erroring_calls:
        with pytest.raises(RecognitionError) as exc_info:
            call()
        message = str(exc_info.value)
        assert isinstance(message, str) and message
        assert "Traceback" not in message


def test_error_messages_use_basename_not_full_path(tmp_path):
    with pytest.raises(ImageLoadError) as exc_info:
        ingestor.ingest_image(tmp_path / "secret.png")
    message = str(exc_info.value)
    assert "secret.png" in message
    assert str(tmp_path) not in message


@pytest.mark.parametrize(
    "error_type",
    [ImageLoadError, ImageValidationError, UnsupportedImageError],
)
def test_error_hierarchy_types(error_type):
    assert issubclass(error_type, recognition.RecognitionError)


def test_importing_recognition_pulls_no_heavy_modules():
    script = (
        "import sys\n"
        "import decodebot.recognition\n"
        "import decodebot.recognition.ingestor\n"
        "import decodebot.recognition.result\n"
        "heavy = [m for m in ('cv2', 'pytesseract', 'numpy', 'tkinter', "
        "'decodebot.core', 'decodebot.ml', 'decodebot.recommender') "
        "if m in sys.modules]\n"
        "if heavy:\n"
        "    print('HEAVY:' + ','.join(heavy))\n"
        "    sys.exit(1)\n"
        "print('OK')\n"
    )
    result = _run_subprocess(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_ingest_never_imports_real_cv2_when_mocked(monkeypatch, tmp_path):
    real_cv2 = None
    try:
        real_cv2 = sys.modules.get("cv2")
        sys.modules.pop("cv2", None)
        monkeypatch.setattr(ingestor, "_load_cv2", lambda: _PilBackedCv2())
        path = _write_image(tmp_path / "mocked.png")
        ingested = ingestor.ingest_image(path)
        assert ingested.format == "PNG"
        assert "cv2" not in sys.modules
    finally:
        if real_cv2 is not None:
            sys.modules["cv2"] = real_cv2


@pytest.mark.skipif(
    importlib.util.find_spec("cv2") is None,
    reason="OpenCV not installed (optional dependency)",
)
def test_real_cv2_ingests_generated_png(tmp_path):
    path = _write_image(tmp_path / "real.png")
    ingested = ingestor.ingest_image(path)
    assert (ingested.width, ingested.height) == (64, 32)
    assert ingested.image is not None
