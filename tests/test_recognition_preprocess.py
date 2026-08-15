"""Week 4 OCR Recognition Engine — preprocessing pipeline tests (FR-253).

TC-OCR-003: each FR-253 stage is verified — grayscale output is single
channel, the Gaussian kernel is applied, deskew corrects a synthetic 3°
skew to within ~0.5°, adaptive thresholding yields a binary (0/255) image,
and the whole pipeline runs headless.

TC-OCR-004: a blank (all-black or all-white) image runs the pipeline without
crashing.

These tests exercise the real OpenCV pipeline when OpenCV is installed and
skip cleanly otherwise (CI must never require OpenCV — FR-262). The pure
decision helpers (``normalize_angle``/``should_deskew``) are tested with no
dependencies at all.

Import discipline: ``numpy`` is only pulled lazily via ``importlib`` so the
ML-isolation gate stays green; ``cv2`` is obtained through the module-level
``pytest.importorskip`` (never an ``import cv2`` statement).

Reference: SPEC.md Part IV — Category T3 (FR-253), NFR-093.
"""

import importlib
import os
import time

import pytest

import decodebot.recognition.preprocess as preprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_IMAGE = os.path.join(PROJECT_ROOT, "samples", "sample_text.png")

cv2 = pytest.importorskip("cv2")


def _np():
    return importlib.import_module("numpy")


def _rect_image(width=200, height=60):
    """A filled dark horizontal bar on white — a synthetic text line."""
    np = _np()
    image = np.full((height, width), 255, dtype=np.uint8)
    image[20:40, :] = 0
    return image


def _rotate(image, angle_deg):
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def _blank_image(color=0):
    np = _np()
    return np.full((120, 180), color, dtype=np.uint8)


# --- Pure decision helpers (no cv2/numpy needed) -----------------------------


def test_should_deskew_threshold_edges():
    assert preprocess.should_deskew(0.0) is False
    assert preprocess.should_deskew(0.4) is False
    assert preprocess.should_deskew(0.6) is True
    assert preprocess.should_deskew(-0.6) is True
    assert preprocess.should_deskew(3.0) is True


def test_should_deskew_custom_threshold():
    assert preprocess.should_deskew(0.7, threshold=1.0) is False
    assert preprocess.should_deskew(1.4, threshold=1.0) is True


def test_normalize_angle_cases():
    assert preprocess.normalize_angle(0.0) == 0.0
    assert preprocess.normalize_angle(3.0) == 3.0
    assert preprocess.normalize_angle(-2.5) == -2.5
    assert preprocess.normalize_angle(-45.0) == -45.0
    assert preprocess.normalize_angle(-60.0) == 30.0
    assert preprocess.normalize_angle(-87.0) == 3.0


# --- Real pipeline stages (skipped when OpenCV is absent) --------------------


def test_to_grayscale_output_is_single_channel():
    np = _np()
    color = _np().repeat(_rect_image()[:, :, None], 3, axis=2)
    gray = preprocess.to_grayscale(color)
    assert gray.ndim == 2
    assert gray.dtype == np.uint8


def test_to_grayscale_passthrough_for_single_channel():
    gray_in = _rect_image()
    assert preprocess.to_grayscale(gray_in) is gray_in


def test_blur_applies_gaussian_kernel():
    np = _np()
    sharp = np.zeros((60, 60), dtype=np.uint8)
    sharp[15:45, 15:45] = 255
    blurred = preprocess.blur(sharp, kernel_size=5, sigma=1.0)
    assert blurred.shape == sharp.shape
    assert blurred.dtype == np.uint8
    assert float(blurred.std()) < float(sharp.std())
    assert 0 < int(blurred[15, 15]) < 255


def test_blur_even_kernel_size_is_bumped_to_odd():
    sharp = _blank_image(0)
    sharp[20:100, 20:160] = 255
    blurred = preprocess.blur(sharp, kernel_size=4)
    assert blurred.shape == sharp.shape


def test_deskew_corrects_synthetic_3_degree_skew():
    for angle in (3.0, -3.0):
        skewed = _rotate(_rect_image(), angle)
        deskewed, detected, applied = preprocess.deskew(skewed)
        assert applied is True
        residual = preprocess.estimate_skew(deskewed)
        assert abs(residual) < 0.5, f"residual skew {residual}° for input {angle}°"
        assert deskewed.shape == skewed.shape


def test_deskew_applies_twice_is_idempotent():
    skewed = _rotate(_rect_image(), 2.0)
    once, _, _ = preprocess.deskew(skewed)
    twice, _, applied = preprocess.deskew(once)
    assert applied is False
    assert twice.shape == once.shape


def test_deskew_skips_when_skew_below_half_degree():
    skewed = _rotate(_rect_image(), 0.2)
    _, angle, applied = preprocess.deskew(skewed)
    assert applied is False
    assert abs(angle) <= 0.5


def test_threshold_yields_binary_image():
    np = _np()
    gray = _rect_image()
    binary = preprocess.threshold(gray)
    unique = np.unique(binary)
    assert set(unique.tolist()) <= {0, 255}
    assert binary.ndim == 2


def test_preprocess_pipeline_output_is_binary_single_channel():
    np = _np()
    color = _np().repeat(_rect_image()[:, :, None], 3, axis=2)
    binary, metadata = preprocess.preprocess_image(color)
    assert binary.ndim == 2
    assert binary.dtype == np.uint8
    assert set(np.unique(binary).tolist()) <= {0, 255}
    assert isinstance(metadata["deskew_applied"], bool)
    assert isinstance(metadata["detected_angle"], float)


def test_preprocess_metadata_reflects_deskew():
    color = _np().repeat(_rect_image()[:, :, None], 3, axis=2)
    _, metadata = preprocess.preprocess_image(color)
    assert metadata["deskew_applied"] is False
    assert abs(metadata["detected_angle"]) <= 0.5


def test_blank_black_image_runs_pipeline_without_crash():
    binary, metadata = preprocess.preprocess_image(_blank_image(0))
    assert binary is not None
    assert metadata["deskew_applied"] is False


def test_blank_white_image_runs_pipeline_without_crash():
    binary, metadata = preprocess.preprocess_image(_blank_image(255))
    assert binary is not None
    assert metadata["deskew_applied"] is False


def test_estimate_skew_returns_zero_for_blank_image():
    assert preprocess.estimate_skew(_blank_image(0)) == 0.0
    assert preprocess.estimate_skew(_blank_image(255)) == 0.0


def test_pipeline_runs_on_fixture_under_one_second():
    assert os.path.isfile(FIXTURE_IMAGE)
    image = cv2.imread(FIXTURE_IMAGE)
    assert image is not None
    start = time.monotonic()
    binary, _ = preprocess.preprocess_image(image)
    elapsed = time.monotonic() - start
    assert binary is not None
    assert elapsed < 1.0, f"pipeline took {elapsed:.3f}s on the fixture (NFR-093)"
