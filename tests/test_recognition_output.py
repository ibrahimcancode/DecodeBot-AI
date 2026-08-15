"""Week 4 OCR Recognition Engine — structured output & --save tests (FR-258).

TC-OCR-006/007/008: the four FR-257 statuses are constructible and rendered;
``RecognitionResult`` exposes the FR-258 fields; the optional ``--save``
output writes a ``.txt`` file and never overwrites an existing file unless
``rec_overwrite=true`` (FR-258) and survives a non-writable output directory
with a friendly error (FR-258 edge case).

Pure-local tests — no OCR binary required.

Reference: SPEC.md Part IV — Category T6 (FR-256-FR-258).
"""

import os

import pytest

from decodebot.recognition.result import save_text_output
from decodebot import recognition as recognition


def _sample_words():
    return (
        recognition.Word(text="hello", confidence=0.95, bbox=(10, 20, 60, 15), order=0),
        recognition.Word(text="world", confidence=0.88, bbox=(80, 20, 55, 15), order=1),
    )


def test_each_status_is_constructible_and_rendered():
    samples = {
        recognition.STATUS_ACCEPTED: recognition.build_result(
            _sample_words(), confidence_threshold=0.80
        ),
        recognition.STATUS_LOW_CONFIDENCE: recognition.build_result(
            (_word_lo(),), confidence_threshold=0.80
        ),
        recognition.STATUS_NO_TEXT: recognition.build_result((), confidence_threshold=0.80),
        recognition.STATUS_ERROR: recognition.error_result("boom"),
    }
    assert samples[recognition.STATUS_ACCEPTED].render_status() == "Accepted"
    assert samples[recognition.STATUS_LOW_CONFIDENCE].render_status() == "Low confidence"
    assert samples[recognition.STATUS_NO_TEXT].render_status() == "No text"
    assert samples[recognition.STATUS_ERROR].render_status() == "Error"


def _word_lo():
    return recognition.Word(text="mumble", confidence=0.1, bbox=(5, 5, 10, 10), order=0)


def test_result_exposes_fr258_fields():
    result = recognition.build_result(
        _sample_words(),
        full_text="hello world",
        image_path="samples/sample_text.png",
        psm=6,
        confidence_threshold=0.80,
        duration_ms=123.0,
        deskew_applied=False,
        detected_angle=0.0,
    )
    for field_name in (
        "status",
        "text",
        "full_text",
        "words",
        "low_confidence_words",
        "overall_confidence",
        "image_path",
        "psm",
        "confidence_threshold",
        "duration_ms",
        "deskew_applied",
        "detected_angle",
        "message",
    ):
        assert hasattr(result, field_name), f"RecognitionResult missing {field_name}"


def test_result_word_count_and_character_count():
    result = recognition.build_result(_sample_words(), confidence_threshold=0.80)
    assert result.word_count == 2
    assert result.character_count == len("hello world")


def test_format_confidence_and_range_helpers():
    assert recognition.format_confidence(0.82) == "82%"
    assert recognition.format_confidence(None) == "N/A"
    assert recognition.format_confidence(float("nan")) == "N/A"
    assert recognition.format_confidence(float("inf")) == "N/A"
    words = _sample_words()
    assert recognition.confidence_range_text(words) == "88%-95%"
    assert recognition.confidence_range_text((recognition.Word("x", 1.0, ()),)) == "100%"
    assert recognition.confidence_range_text(()) == "N/A"


def test_save_writes_text_file_with_stem(tmp_path):
    path = save_text_output(
        "hello world",
        "samples/sample_text.png",
        output_dir=str(tmp_path),
        overwrite=False,
    )
    written = os.path.join(str(tmp_path), "sample_text.txt")
    assert path == written
    assert os.path.isfile(written)
    assert open(written, encoding="utf-8").read() == "hello world"


def test_save_creates_missing_output_directory(tmp_path):
    nested = tmp_path / "nested" / "dir"
    path = save_text_output("data", "img.png", output_dir=str(nested), overwrite=False)
    assert os.path.isfile(path)


def test_save_refuses_overwrite_without_rec_overwrite(tmp_path):
    target = os.path.join(str(tmp_path), "img.txt")
    os.makedirs(str(tmp_path), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write("original")
    with pytest.raises(recognition.OutputError) as exc_info:
        save_text_output("new content", "img.png", output_dir=str(tmp_path), overwrite=False)
    assert "already exists" in str(exc_info.value)
    assert open(target, encoding="utf-8").read() == "original"


def test_save_overwrites_with_rec_overwrite(tmp_path):
    target = os.path.join(str(tmp_path), "img.txt")
    with open(target, "w", encoding="utf-8") as handle:
        handle.write("original")
    path = save_text_output("new content", "img.png", output_dir=str(tmp_path), overwrite=True)
    assert path == target
    assert open(target, encoding="utf-8").read() == "new content"


def test_save_non_writable_directory_is_friendly(tmp_path, monkeypatch):
    parent_file = tmp_path / "blocker"
    parent_file.write_text("x")
    target_dir = str(parent_file / "sub")
    with pytest.raises(recognition.OutputError) as exc_info:
        save_text_output("text", "img.png", output_dir=target_dir, overwrite=False)
    assert "Could not create output directory" in str(exc_info.value)


def test_save_output_error_is_recognition_error():
    assert issubclass(recognition.OutputError, recognition.RecognitionError)
