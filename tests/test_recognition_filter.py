"""Week 4 OCR Recognition Engine — confidence filtering tests (FR-256, FR-257).

TC-OCR-006: words with confidence below the 80% threshold are routed to
``low_confidence_words`` and excluded from the accepted text; accepted words
are >= threshold; unusable words (empty text, empty bounding box, ``None``
confidence) are excluded from both lists. Status derivation
(``accepted``/``low_confidence``/``no_text``) and confidence aggregation are
covered.

Pure-Python tests — no image decoding required.

Reference: SPEC.md Part IV — Categories T5 (FR-256, FR-257).
"""

import pytest

from decodebot.recognition.result import Word
from decodebot import recognition as recognition

FILTER = recognition


def _word(text, confidence, bbox=(10, 10, 60, 20)):
    return Word(text=text, confidence=confidence, bbox=bbox, order=0)


def test_default_confidence_threshold_is_eighty_percent():
    assert recognition.DEFAULT_CONFIDENCE_THRESHOLD == 0.80


def test_filter_routes_below_threshold_to_low_confidence():
    accepted, low = recognition.filter_words(
        [_word("good", 0.95), _word("maybe", 0.75)],
        threshold=0.80,
    )
    assert [w.text for w in accepted] == ["good"]
    assert [w.text for w in low] == ["maybe"]


def test_filter_threshold_boundary_accepts_on_threshold():
    accepted, low = recognition.filter_words(
        [_word("edge", 0.80), _word("below", 0.79)],
        threshold=0.80,
    )
    assert [w.text for w in accepted] == ["edge"]
    assert [w.text for w in low] == ["below"]


def test_filter_excludes_none_confidence_words_entirely():
    accepted, low = recognition.filter_words(
        [_word("sentinel", -1.0), Word(text="x", confidence=None, bbox=(0, 0, 1, 1))],
        threshold=0.80,
    )
    assert accepted == ()
    assert low == ()


def test_filter_excludes_empty_text_and_empty_bbox():
    bad_text = Word(text="", confidence=0.99, bbox=(0, 0, 1, 1))
    bad_bbox = Word(text="stray", confidence=0.99, bbox=())
    accepted, low = recognition.filter_words([bad_text, bad_bbox], threshold=0.80)
    assert accepted == ()
    assert low == ()


def test_filter_preserves_reading_order():
    words = [
        _word("two", 0.95, bbox=(100, 10, 60, 20)),
        _word("one", 0.95, bbox=(10, 10, 60, 20)),
        _word("bad", 0.10, bbox=(200, 10, 60, 20)),
    ]
    accepted, low = recognition.filter_words(words, threshold=0.80)
    assert [w.text for w in accepted] == ["two", "one"]
    assert [w.text for w in low] == ["bad"]


def test_classify_status_accepted():
    accepted = (_word("good", 0.9),)
    assert recognition.classify_status(accepted, ()) == recognition.STATUS_ACCEPTED


def test_classify_status_low_confidence():
    low = (_word("bad", 0.1),)
    assert recognition.classify_status((), low) == recognition.STATUS_LOW_CONFIDENCE


def test_classify_status_no_text_when_empty():
    assert recognition.classify_status((), ()) == recognition.STATUS_NO_TEXT


def test_classify_status_all_four_values():
    assert recognition.ALL_STATUSES == (
        recognition.STATUS_ACCEPTED,
        recognition.STATUS_LOW_CONFIDENCE,
        recognition.STATUS_NO_TEXT,
        recognition.STATUS_ERROR,
    )


def test_aggregate_confidence_is_mean_of_accepted():
    accepted = (_word("a", 0.8), _word("b", 1.0))
    assert recognition.aggregate_confidence(accepted) == 0.9


def test_aggregate_confidence_empty_is_none():
    assert recognition.aggregate_confidence(()) is None


def test_aggregate_confidence_single_word():
    assert recognition.aggregate_confidence((_word("only", 0.9),)) == 0.9


@pytest.mark.parametrize(
    "words,threshold,expected_status,expected_text",
    [
        (
            [_word("hello", 0.95), _word("world", 0.9)],
            0.80,
            recognition.STATUS_ACCEPTED,
            "hello world",
        ),
        (
            [_word("mumble", 0.5)],
            0.80,
            recognition.STATUS_LOW_CONFIDENCE,
            "",
        ),
        (
            [_word("x", None)],
            0.80,
            recognition.STATUS_NO_TEXT,
            "",
        ),
        ([], 0.80, recognition.STATUS_NO_TEXT, ""),
    ],
)
def test_build_result_status_and_text(words, threshold, expected_status, expected_text):
    result = recognition.build_result(words, full_text="full text", confidence_threshold=threshold)
    assert result.status == expected_status
    assert result.text == expected_text
    assert result.full_text == "full text"
    assert result.confidence_threshold == threshold


def test_build_result_carries_metadata_fields():
    result = recognition.build_result(
        [_word("ok", 0.95)],
        full_text="ok",
        image_path="samples/sample_text.png",
        psm=7,
        confidence_threshold=0.90,
        duration_ms=42.5,
        deskew_applied=True,
        detected_angle=-3.12,
        processed_image="binary-ref",
    )
    assert result.image_path == "samples/sample_text.png"
    assert result.psm == 7
    assert result.confidence_threshold == 0.90
    assert result.duration_ms == 42.5
    assert result.deskew_applied is True
    assert result.detected_angle == -3.12
    assert result.processed_image == "binary-ref"
    assert len(result.words) == 1
    assert result.low_confidence_words == ()
    assert result.overall_confidence == 0.95


def test_build_result_low_confidence_populates_low_words():
    result = recognition.build_result(
        [_word("mumble", 0.5)],
        confidence_threshold=0.80,
    )
    assert result.status == recognition.STATUS_LOW_CONFIDENCE
    assert [w.text for w in result.words] == []
    assert [w.text for w in result.low_confidence_words] == ["mumble"]
    assert result.text == ""
    assert result.overall_confidence is None


def test_error_result_has_error_status_and_message():
    result = recognition.error_result(
        "Tesseract OCR is not installed...",
        image_path="samples/x.png",
        psm=6,
        duration_ms=10.0,
    )
    assert result.status == recognition.STATUS_ERROR
    assert result.message == "Tesseract OCR is not installed..."
    assert result.image_path == "samples/x.png"
    assert result.text == ""
    assert result.words == ()


def test_build_result_default_status_message_for_no_text():
    result = recognition.build_result([], confidence_threshold=0.80)
    assert result.status == recognition.STATUS_NO_TEXT
    assert result.message == "No text detected in this image."


def test_build_result_message_override_respected():
    result = recognition.build_result(
        [_word("ok", 0.95)], message="custom", confidence_threshold=0.80
    )
    assert result.message == "custom"


def test_build_result_ignores_invalid_words_in_full_text_only():
    """Full text keeps everything; filtering excludes unusable words."""
    words = [_word("ok", 0.95), _word("none-conf", None)]
    result = recognition.build_result(words, full_text="ok none-conf", confidence_threshold=0.80)
    assert [w.text for w in result.words] == ["ok"]
    assert result.full_text == "ok none-conf"
    assert result.text == "ok"
