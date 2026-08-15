"""Week 4 OCR Recognition Engine — Tesseract OCR wrapper tests (FR-254, FR-255).

TC-OCR-005: a fixture image yields expected words with per-word confidence
values (verified against a deterministic mocked Tesseract dataset; the
optional real-Tesseract run is exercised when the binary is present).

TC-OCR-010: simulated missing ``pytesseract`` dependency and missing
Tesseract binary produce friendly, actionable errors and zero unhandled
exceptions (FR-255).

All heavy behavior is tested against an injected fake ``pytesseract`` so CI
never requires pytesseract/Tesseract installed (FR-262).

Reference: SPEC.md Part IV — Category T4 (FR-254-FR-255), FR-262.
"""

import os

import pytest

import decodebot.recognition.ocr_engine as ocr_engine
from decodebot.recognition.errors import (
    DependencyUnavailableError,
    OcrError,
    UnsupportedPsmError,
)
from decodebot.recognition.result import Word

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_IMAGE = os.path.join(PROJECT_ROOT, "samples", "sample_text.png")


class FakeOutput:
    DICT = "dict"


class FakePytesseract:
    """Deterministic stand-in for the pytesseract module (FR-262)."""

    Output = FakeOutput

    def __init__(self, data=None, version_ok=True, data_error=None):
        self._data = data or {}
        self._version_ok = version_ok
        self._data_error = data_error
        self.calls = []

    def get_tesseract_version(self):
        if not self._version_ok:
            raise RuntimeError("Tesseract binary not found on PATH")
        return "5.3.0"

    def image_to_data(self, image, config=None, output_type=None):
        self.calls.append({"image": image, "config": config, "output_type": output_type})
        if self._data_error is not None:
            raise self._data_error
        return self._data


def _make_data(words):
    """Build an image_to_data DICT from (text, conf, bbox, block, line) rows."""
    keys = [
        "level",
        "page_num",
        "block_num",
        "par_num",
        "line_num",
        "word_num",
        "left",
        "top",
        "width",
        "height",
        "conf",
        "text",
    ]
    data = {key: [] for key in keys}
    for text, conf, left, top, width, height, block, line in words:
        data["level"].append(5)
        data["page_num"].append(1)
        data["block_num"].append(block)
        data["par_num"].append(1)
        data["line_num"].append(line)
        data["word_num"].append(len(data["level"]))
        data["left"].append(left)
        data["top"].append(top)
        data["width"].append(width)
        data["height"].append(height)
        data["conf"].append(conf)
        data["text"].append(text)
    return data


def _run_with_fake(monkeypatch, fake, image="binary-image", psm=6):
    monkeypatch.setattr(ocr_engine, "_load_pytesseract", lambda: fake)
    return ocr_engine.run_ocr(image, psm=psm)


def test_supported_psm_modes_and_default():
    assert ocr_engine.SUPPORTED_PSM_MODES == (3, 6, 7, 11)
    assert ocr_engine.DEFAULT_PSM == 6


@pytest.mark.parametrize("psm", [3, 6, 7, 11])
def test_validate_psm_accepts_supported_modes(psm):
    assert ocr_engine.validate_psm(psm) == psm
    assert ocr_engine.validate_psm(str(psm)) == psm
    assert ocr_engine.validate_psm(float(psm)) == psm


@pytest.mark.parametrize("psm", [0, 1, 2, 4, 5, 8, 9, 10, 12, 13, "auto", None])
def test_validate_psm_rejects_unsupported_modes(psm):
    with pytest.raises(UnsupportedPsmError) as exc_info:
        ocr_engine.validate_psm(psm)
    assert "3, 6, 7, 11" in str(exc_info.value)


def test_run_ocr_extracts_words_with_normalized_confidence(monkeypatch):
    data = _make_data(
        [
            ("Hello", 95, 10, 20, 60, 15, 1, 1),
            ("world", 80, 80, 20, 55, 15, 1, 1),
        ]
    )
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    assert isinstance(output, ocr_engine.OcrOutput)
    assert len(output.words) == 2
    first, second = output.words
    assert first.text == "Hello"
    assert first.confidence == 0.95
    assert first.bbox == (10, 20, 60, 15)
    assert second.confidence == 0.8
    assert output.full_text == "Hello world"
    assert output.psm == 6


def test_run_ocr_sentinel_confidence_maps_to_none(monkeypatch):
    data = _make_data([("fuzzy", -1, 10, 20, 50, 15, 1, 1)])
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    assert output.words[0].confidence is None


def test_run_ocr_skips_blank_text_and_non_word_rows(monkeypatch):
    data = _make_data([("keep", 90, 10, 20, 40, 15, 1, 1)])
    data["level"].append(4)
    data["text"].append("line-level-noise")
    data["conf"].append(88)
    data["level"].append(5)
    data["text"].append("   ")
    data["conf"].append(50)
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    assert [word.text for word in output.words] == ["keep"]


def test_run_ocr_orders_words_in_reading_order(monkeypatch):
    data = _make_data(
        [
            ("second-line", 90, 10, 60, 90, 15, 1, 2),
            ("first-line", 90, 10, 20, 80, 15, 1, 1),
            ("first-x2", 90, 100, 20, 60, 15, 1, 1),
        ]
    )
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    assert [word.text for word in output.words] == ["first-line", "first-x2", "second-line"]
    assert [word.order for word in output.words] == [0, 1, 2]


def test_run_ocr_passes_psm_to_config(monkeypatch):
    fake = FakePytesseract(data={})
    _run_with_fake(monkeypatch, fake, psm=7)
    assert fake.calls[0]["config"] == "--psm 7"
    assert fake.calls[0]["output_type"] == "dict"


def test_run_ocr_uses_default_psm_six(monkeypatch):
    fake = FakePytesseract(data={})
    _run_with_fake(monkeypatch, fake)
    assert fake.calls[0]["config"] == "--psm 6"


def test_run_ocr_empty_data_yields_no_text(monkeypatch):
    fake = FakePytesseract(data={})
    output = _run_with_fake(monkeypatch, fake)
    assert output.words == ()
    assert output.full_text == ""


def test_run_ocr_invalid_geometry_yields_empty_bbox(monkeypatch):
    data = _make_data([("stray", 90, -1, -1, -1, -1, 1, 1)])
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    assert output.words[0].bbox == ()


def test_run_ocr_missing_pytesseract_dependency(monkeypatch):
    def missing():
        raise DependencyUnavailableError(
            "The OCR engine needs the optional package 'pytesseract', which "
            "is not installed. Install the optional OCR dependencies with: "
            "pip install -r requirements-ocr.txt"
        )

    monkeypatch.setattr(ocr_engine, "_load_pytesseract", missing)
    with pytest.raises(DependencyUnavailableError) as exc_info:
        ocr_engine.run_ocr("binary-image", psm=6)
    assert "requirements-ocr.txt" in str(exc_info.value)


def test_run_ocr_missing_tesseract_binary_is_friendly(monkeypatch):
    fake = FakePytesseract(version_ok=False)
    monkeypatch.setattr(ocr_engine, "_load_pytesseract", lambda: fake)
    with pytest.raises(OcrError) as exc_info:
        ocr_engine.run_ocr("binary-image", psm=6)
    message = str(exc_info.value)
    assert "Tesseract OCR is not installed" in message
    assert "Traceback" not in message


def test_run_ocr_image_to_data_failure_is_friendly(monkeypatch):
    fake = FakePytesseract(data_error=RuntimeError("tesseract crashed"))
    monkeypatch.setattr(ocr_engine, "_load_pytesseract", lambda: fake)
    with pytest.raises(OcrError) as exc_info:
        ocr_engine.run_ocr("binary-image", psm=6)
    assert "could not read this image" in str(exc_info.value)


def test_ensure_tesseract_available_passes_when_present(monkeypatch):
    fake = FakePytesseract(version_ok=True)
    monkeypatch.setattr(ocr_engine, "_load_pytesseract", lambda: fake)
    ocr_engine.ensure_tesseract_available()


def test_ensure_tesseract_available_raises_when_missing(monkeypatch):
    fake = FakePytesseract(version_ok=False)
    monkeypatch.setattr(ocr_engine, "_load_pytesseract", lambda: fake)
    with pytest.raises(OcrError) as exc_info:
        ocr_engine.ensure_tesseract_available()
    assert "Tesseract OCR" in str(exc_info.value)


def test_ocr_output_is_frozen_dataclass(monkeypatch):
    data = _make_data([("hi", 90, 0, 0, 20, 10, 1, 1)])
    fake = FakePytesseract(data=data)
    output = _run_with_fake(monkeypatch, fake)
    with pytest.raises(AttributeError):
        output.full_text = "mutated"


def test_word_is_frozen_dataclass():
    word = Word(text="x", confidence=0.9, bbox=(0, 0, 1, 1), order=0)
    with pytest.raises(AttributeError):
        word.text = "mutated"


def test_importing_ocr_engine_pulls_no_heavy_modules():
    import importlib
    import subprocess
    import sys

    script = (
        "import sys\n"
        "import decodebot.recognition.ocr_engine\n"
        "heavy = [m for m in ('cv2', 'pytesseract', 'numpy', 'tkinter', "
        "'decodebot.core', 'decodebot.ml', 'decodebot.recommender') "
        "if m in sys.modules]\n"
        "if heavy:\n"
        "    print('HEAVY:' + ','.join(heavy))\n"
        "    sys.exit(1)\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def _has_cv2_and_pytesseract():
    import importlib.util

    return (
        importlib.util.find_spec("cv2") is not None
        and importlib.util.find_spec("pytesseract") is not None
    )


@pytest.mark.skipif(
    not _has_cv2_and_pytesseract(),
    reason="OpenCV/pytesseract not installed (optional dependencies)",
)
def test_real_env_run_ocr_graceful_and_no_unhandled_error():
    """Real cv2+pytesseract: pipeline runs; binary present → words, else OcrError."""
    import importlib
    import cv2

    image = cv2.imread(FIXTURE_IMAGE)
    assert image is not None
    from decodebot.recognition.preprocess import preprocess_image

    binary, _ = preprocess_image(image)
    try:
        output = ocr_engine.run_ocr(binary, psm=6)
    except OcrError:
        return  # Tesseract binary absent → friendly error (FR-255)
    assert isinstance(output, ocr_engine.OcrOutput)
    assert isinstance(output.full_text, str)
