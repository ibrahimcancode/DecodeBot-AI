"""Wave 4 OCR recognition isolation gate (FR-249, FR-250, NFR-091, NFR-095).

Static and dynamic checks that the ``decodebot.recognition`` package is fully
isolated from the rest of the Chatbot Engine, mirroring
``tests/test_wave3_isolation.py``:

- No engine file (core/rules/plugins/utils/gui/entry point) imports
  ``decodebot.recognition``, ``cv2`` or ``pytesseract`` except the permitted
  wiring files (FR-249).
- No OCR library (``cv2``/``pytesseract``/``numpy``) is imported at module
  scope inside the recognition package — function-level lazy imports only
  (FR-250).
- Recognition modules must not import other DecodeBot subsystems
  (``decodebot.core``/``decodebot.ml``/``decodebot.recommender``) or
  ``tkinter``.
- Importing the recognition package pulls no heavy module into ``sys.modules``,
  performs no OCR, loads no image, and never touches the Tesseract binary.
- Starting the Chatbot Engine (``decodebot.core.app``) must not import the
  recognition package.

Reference: SPEC.md Part IV — FR-249, FR-250, NFR-091, NFR-095.
"""

import ast
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DECODEBOT_DIR = os.path.join(PROJECT_ROOT, "decodebot")
RECOGNITION_DIR = os.path.join(DECODEBOT_DIR, "recognition")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

OCR_LIBRARIES = ("cv2", "pytesseract", "numpy")
OTHER_SUBSYSTEMS = ("decodebot.core", "decodebot.ml", "decodebot.recommender")

_WIRING_FILES = {"main.py", "dispatcher.py", "app_gui.py", "app.py"}


def _py_files(root):
    """Return all .py files under root, excluding hidden dirs and venvs."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if not d.startswith(".") and d not in ("venv", "env", ".venv")
        ]
        for name in filenames:
            if name.endswith(".py"):
                files.append(os.path.join(dirpath, name))
    return files


def _imported_modules(path):
    """Return module names imported by path (any scope)."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        tree = ast.parse(handle.read(), filename=path)
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _top_level_imported_modules(path):
    """Return module names imported at module scope by path."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        tree = ast.parse(handle.read(), filename=path)
    modules = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _is_within(path, directory):
    return os.path.abspath(path).startswith(os.path.abspath(directory) + os.sep)


def _matches(module_name, name):
    return module_name == name or module_name.startswith(name + ".")


def _run_subprocess(script):
    """Run a script in a fresh interpreter and return its completed result."""
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )


def test_recognition_not_imported_by_engine_files():
    """Engine files may not import decodebot.recognition (FR-249)."""
    for py_file in _py_files(DECODEBOT_DIR):
        if _is_within(py_file, RECOGNITION_DIR):
            continue
        for module in _imported_modules(py_file):
            if _matches(module, "decodebot.recognition"):
                if os.path.basename(py_file) not in _WIRING_FILES:
                    pytest.fail(
                        f"decodebot.recognition imported in {py_file}; only "
                        "wiring files may bridge to the recognition package "
                        "(FR-249)."
                    )


def test_ocr_libraries_only_inside_recognition():
    """No cv2/pytesseract import anywhere outside the recognition package."""
    for py_file in _py_files(DECODEBOT_DIR):
        in_recognition = _is_within(py_file, RECOGNITION_DIR)
        if in_recognition:
            continue
        for module in _imported_modules(py_file):
            for library in ("cv2", "pytesseract"):
                if _matches(module, library):
                    pytest.fail(
                        f"{module} imported in {py_file} — cv2/pytesseract are "
                        "allowed only inside decodebot/recognition/ (FR-249)."
                    )


@pytest.mark.parametrize("py_file", _py_files(RECOGNITION_DIR))
def test_no_module_scope_ocr_imports_in_recognition(py_file):
    """Recognition modules may not import OCR libs at module scope (FR-250)."""
    for module in _top_level_imported_modules(py_file):
        for library in OCR_LIBRARIES:
            assert not _matches(
                module, library
            ), f"{module} imported at module scope in {py_file} (FR-250)"


@pytest.mark.parametrize("py_file", _py_files(RECOGNITION_DIR))
def test_no_other_subsystem_or_tk_imports_in_recognition(py_file):
    """Recognition must not import other subsystems or tkinter (FR-249)."""
    for module in _imported_modules(py_file):
        for subsystem in OTHER_SUBSYSTEMS + ("tkinter",):
            assert not _matches(module, subsystem), f"{module} imported in {py_file} (FR-249)"


def test_importing_recognition_is_lazy_and_side_effect_free():
    """Importing the package pulls no heavy modules and does no work."""
    script = (
        "import sys\n"
        "import decodebot.recognition as recognition\n"
        "import decodebot.recognition.ingestor as ingestor\n"
        "import decodebot.recognition.result as result\n"
        "present = [m for m in ("
        "'cv2', 'pytesseract', 'numpy', 'PIL', 'sklearn', 'pandas', "
        "'matplotlib', 'joblib', 'tkinter', 'decodebot.core', "
        "'decodebot.ml', 'decodebot.recommender') if m in sys.modules]\n"
        "if present:\n"
        "    print('PRESENT:' + ','.join(present))\n"
        "    sys.exit(1)\n"
        "print('OK')\n"
    )
    result = _run_subprocess(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_engine_startup_does_not_import_recognition():
    """decodebot.core.app starts without touching recognition (FR-250)."""
    script = (
        "import sys\n"
        "import decodebot.core.app\n"
        "for m in sys.modules:\n"
        "    if m == 'decodebot.recognition' "
        "or m.startswith('decodebot.recognition.'):\n"
        "        print('IMPORTED:' + m)\n"
        "        sys.exit(1)\n"
        "print('OK')\n"
    )
    result = _run_subprocess(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_recognition_w4_m1_modules_are_discoverable():
    """W4-M1 recognition module set exists on disk."""
    for module_name in ("__init__", "errors", "dependencies", "ingestor", "result"):
        assert os.path.isfile(
            os.path.join(RECOGNITION_DIR, module_name + ".py")
        ), f"decodebot/recognition/{module_name}.py is missing"
