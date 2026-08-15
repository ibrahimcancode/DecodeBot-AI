"""Unit tests for Streamlit web-demo helpers (no Streamlit UI runtime)."""

from pathlib import Path

from streamlit_helpers import (
    classifier_label,
    combine_skills,
    exit_message,
    iris_preset_defaults,
    psm_label,
    reset_message,
    safe_upload_suffix,
    sample_image_path,
    welcome_message,
)


def test_welcome_message_includes_bot_and_version():
    text = welcome_message("DecodeBot", "3.1.0")
    assert "DecodeBot AI v3.1.0" in text
    assert "help" in text
    assert "recommend" in text


def test_reset_and_exit_messages():
    assert "friend" in reset_message(None)
    assert "Ada" in reset_message("Ada")
    farewell = exit_message(12, "1m 5s")
    assert "12 messages" in farewell
    assert "1m 5s" in farewell


def test_combine_skills_merges_tags_and_custom():
    assert combine_skills(["Python", "SQL"], "") == "Python, SQL"
    assert combine_skills(["Python"], " ML , pytorch , ") == "Python, ML, pytorch"
    assert combine_skills([], "  ") == ""


def test_iris_preset_defaults():
    assert iris_preset_defaults("Iris-Setosa (5.1, 3.5, 1.4, 0.2)") == (
        5.1,
        3.5,
        1.4,
        0.2,
    )
    assert iris_preset_defaults("Custom") == (5.8, 3.0, 4.2, 1.3)


def test_sample_image_path_points_at_fixture():
    path = sample_image_path(Path(__file__).resolve().parent.parent)
    assert path.name == "sample_text.png"
    assert path.parent.name == "samples"
    assert path.is_file()


def test_safe_upload_suffix_is_cross_platform():
    assert safe_upload_suffix("photo.PNG") == "_photo.png"
    assert safe_upload_suffix(r"C:\Users\me\evil..name.jpg") == "_evil..name.jpg"
    # Path traversal / separators must not survive into the suffix.
    assert "/" not in safe_upload_suffix("../../etc/passwd.png")
    assert "\\" not in safe_upload_suffix("..\\windows\\file.jpeg")
    assert safe_upload_suffix("weird name!!.pdf") == "_weird_name_.png"


def test_classifier_and_psm_labels():
    assert "KNN" in classifier_label("knn")
    assert classifier_label("unknown_algo") == "unknown_algo"
    assert psm_label(6).startswith("6")
    assert psm_label(99) == "99"
