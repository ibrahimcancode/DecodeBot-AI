"""Lazy optional-dependency loading for the OCR engine (FR-250, FR-255).

``opencv-python-headless`` and ``pytesseract`` are *optional* dependencies:
the Chatbot, ML and Recommender engines must keep working with neither of
them installed (FR-250), and CI must never require them (FR-262). This module
centralises the *only* sanctioned way those libraries may be imported inside
the recognition package — a function-level helper that raises the friendly
:class:`DependencyUnavailableError` with actionable install guidance when a
dependency is absent (FR-255).

Import discipline (FR-249, FR-250):
    - No ``cv2``/``pytesseract``/``numpy`` import at module scope anywhere in
      the recognition package; callers use :func:`import_optional` inside the
      function that needs the library.
    - Merely importing the recognition package therefore has zero heavy side
      effects and never touches the Tesseract binary or an image on disk.

Reference: SPEC.md Part IV — FR-249, FR-250, FR-255.
"""

import importlib

from decodebot.recognition.errors import DependencyUnavailableError

REQUIRED_MODULES: dict[str, str] = {
    "cv2": "opencv-python-headless",
    "pytesseract": "pytesseract",
    "numpy": "numpy",
}
"""Module name -> pip distribution name used in the install guidance (FR-255)."""

OCR_INSTALL_HINT = "Install the optional OCR dependencies with: pip install -r requirements-ocr.txt"
"""High-level guidance shown whenever any OCR dependency is missing (FR-255)."""


def import_optional(module_name: str):
    """Lazily import and return ``module_name`` or raise a friendly error.

    Args:
        module_name: A top-level importable module name (e.g. ``"cv2"``,
            ``"pytesseract"``, ``"numpy"``).

    Returns:
        The imported module object.

    Raises:
        DependencyUnavailableError: When the module is not installed. The
            message names the missing pip distribution and gives the exact
            install command (FR-250, FR-255).

    Reference: SPEC.md Part IV — FR-250, FR-255.
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        distribution = REQUIRED_MODULES.get(module_name, module_name)
        raise DependencyUnavailableError(
            f"The OCR engine needs the optional package '{distribution}', "
            f"which is not installed. {OCR_INSTALL_HINT}"
        ) from exc
