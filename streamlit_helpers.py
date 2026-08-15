"""Pure helpers for the Streamlit web demo (no Streamlit UI side effects).

Kept separate from ``streamlit_app.py`` so unit tests can exercise business
helpers without importing Streamlit's script runtime.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_SAFE_SUFFIX_RE = re.compile(r"[^A-Za-z0-9._-]+")


def welcome_message(bot_name: str, version: str) -> str:
    """Build the initial assistant greeting shown in the chat tab."""
    return (
        f"Hello! I am **{bot_name} AI v{version}**, a 100% rule-based "
        "conversational agent.\n\n"
        "Type a message or try commands like `help`, `train`, `explore`, "
        "`recommend`, or `stats`!"
    )


def reset_message(user_name: str | None) -> str:
    """Build the post-reset assistant message."""
    who = user_name or "friend"
    return f"Session reset. How can I help you today, {who}?"


def exit_message(message_count: int, duration: str) -> str:
    """Build the EXIT intent farewell shown in the web chat."""
    return (
        f"Goodbye! We exchanged {message_count} messages over {duration}. " "Thanks for chatting!"
    )


def combine_skills(selected_tags: list[str], custom_text: str) -> str:
    """Merge multiselect tags and freeform comma-separated skills."""
    combined: list[str] = list(selected_tags)
    if custom_text.strip():
        combined.extend(s.strip() for s in custom_text.split(",") if s.strip())
    return ", ".join(combined)


def iris_preset_defaults(preset: str) -> tuple[float, float, float, float]:
    """Map an Iris preset label to (sepal_l, sepal_w, petal_l, petal_w)."""
    presets = {
        "Iris-Setosa (5.1, 3.5, 1.4, 0.2)": (5.1, 3.5, 1.4, 0.2),
        "Iris-Versicolor (6.0, 2.7, 5.1, 1.6)": (6.0, 2.7, 5.1, 1.6),
        "Iris-Virginica (6.9, 3.1, 5.4, 2.1)": (6.9, 3.1, 5.4, 2.1),
    }
    return presets.get(preset, (5.8, 3.0, 4.2, 1.3))


def sample_image_path(base_dir: str | Path | None = None) -> Path:
    """Return the bundled OCR fixture path (cross-platform)."""
    root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
    return root / "samples" / "sample_text.png"


def safe_upload_suffix(filename: str) -> str:
    """Build a safe tempfile suffix from an uploaded filename.

    Uses only the basename and strips path separators / unsafe characters so
    Linux and Windows behave the same (no Windows-only path assumptions).
    """
    name = os.path.basename(filename.replace("\\", "/"))
    stem = Path(name).stem or "upload"
    ext = Path(name).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        ext = ".png"
    safe_stem = _SAFE_SUFFIX_RE.sub("_", stem)[:40] or "upload"
    return f"_{safe_stem}{ext}"


def classifier_label(key: str) -> str:
    """Human-readable classifier name for the ML playground selectbox."""
    labels = {
        "knn": "K-Nearest Neighbors (KNN)",
        "decision_tree": "Decision Tree",
        "logistic_regression": "Logistic Regression",
        "svm": "Support Vector Machine (SVM)",
        "random_forest": "Random Forest",
    }
    return labels.get(key, key)


def psm_label(psm: int) -> str:
    """Human-readable Tesseract PSM label."""
    labels = {
        6: "6 — Uniform block of text (Default)",
        3: "3 — Fully automatic page segmentation",
        7: "7 — Single text line",
        11: "11 — Sparse text finding",
    }
    return labels.get(psm, str(psm))
