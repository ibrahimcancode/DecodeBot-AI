"""ML dependency isolation gate (FR-229, NFR-072).

Static scan asserting that ``scikit-learn``/``pandas``/``numpy``/
``matplotlib``/``joblib`` are imported only inside ``decodebot/ml/`` and its
dedicated tests — never in the Chatbot Engine (core/rules/plugins/utils/gui)
or the entry point. Also asserts the ML package is not imported by engine
files except the permitted wiring.
"""

import ast
import os

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DECODEBOT_DIR = os.path.join(PROJECT_ROOT, "decodebot")
ML_DIR = os.path.join(DECODEBOT_DIR, "ml")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

ML_LIBRARIES = ("sklearn", "pandas", "numpy", "matplotlib", "joblib")

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
    """Return module names imported by path (top-level names)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read(), filename=path)
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _is_within(path, directory):
    return os.path.abspath(path).startswith(os.path.abspath(directory) + os.sep)


def _matches_library(module_name, library):
    return module_name == library or module_name.startswith(library + ".")


def _contains_ml_reference(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return "decodebot.ml" in f.read()


@pytest.mark.parametrize("py_file", _py_files(PROJECT_ROOT))
def test_ml_libraries_only_inside_ml_zone(py_file):
    """No ML library import outside decodebot/ml and its dedicated tests."""
    in_ml = _is_within(py_file, ML_DIR)
    in_tests = _is_within(py_file, TESTS_DIR)
    dedicated_ml_test = in_tests and _contains_ml_reference(py_file)

    if in_ml or dedicated_ml_test:
        return

    for module in _imported_modules(py_file):
        for library in ML_LIBRARIES:
            if _matches_library(module, library):
                pytest.fail(
                    f"ML library '{module}' imported in {py_file} — only "
                    "allowed inside decodebot/ml/ and its dedicated tests "
                    "(FR-229)."
                )


def test_ml_package_not_imported_by_engine_files():
    """Engine files may not import decodebot.ml except permitted wiring."""
    for py_file in _py_files(DECODEBOT_DIR):
        if _is_within(py_file, ML_DIR):
            continue
        for module in _imported_modules(py_file):
            if module == "decodebot.ml" or module.startswith("decodebot.ml."):
                if os.path.basename(py_file) not in _WIRING_FILES:
                    pytest.fail(
                        f"decodebot.ml imported in {py_file}; only wiring "
                        "files may bridge to the ML Engine (FR-229)."
                    )


def test_main_py_does_not_import_ml_libraries():
    """Entry point must not import ML libraries directly (FR-229 edge)."""
    main_py = os.path.join(PROJECT_ROOT, "main.py")
    for module in _imported_modules(main_py):
        for library in ML_LIBRARIES:
            assert not _matches_library(
                module, library
            ), f"main.py must not import ML library '{module}' directly"


def test_ml_package_modules_are_discoverable():
    """Every ML Engine module exists on disk (Phases 16-21 module set)."""
    for module_name in (
        "dataset",
        "dataset_loader",
        "dataset_validator",
        "preprocessor",
        "trainer",
        "predictor",
        "evaluator",
        "model_manager",
        "visualization",
        "app_ml",
    ):
        assert os.path.isfile(
            os.path.join(ML_DIR, module_name + ".py")
        ), f"decodebot/ml/{module_name}.py is missing"
