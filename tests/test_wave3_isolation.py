"""Wave 3 recommender isolation gate (FR-233, FR-234, NFR-088).

Static and dynamic checks that the ``decodebot.recommender`` package is fully
isolated from the rest of the Chatbot Engine:

- No engine file (core/rules/plugins/utils/gui/entry point) imports
  ``decodebot.recommender`` except the permitted wiring files.
- No third-party ML library (sklearn/pandas/numpy/matplotlib/joblib), Tk,
  or other DecodeBot subsystem (``decodebot.ml`` / ``decodebot.core``) is
  imported at module scope inside the recommender package — function-level
  lazy imports are allowed (FR-234).
- Importing the recommender package must not pull those heavy modules into
  ``sys.modules`` and must not auto-load any corpus (no dataset side effect).
- Starting the Chatbot Engine (``decodebot.core.app``) must not import the
  recommender package.

Reference: SPEC.md Part III — FR-233, FR-234, NFR-088.
"""

import ast
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DECODEBOT_DIR = os.path.join(PROJECT_ROOT, "decodebot")
RECOMMENDER_DIR = os.path.join(DECODEBOT_DIR, "recommender")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

ML_LIBRARIES = ("sklearn", "pandas", "numpy", "matplotlib", "joblib")
OTHER_SUBSYSTEMS = ("decodebot.ml", "decodebot.core")

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


def test_recommender_not_imported_by_engine_files():
    """Engine files may not import decodebot.recommender (FR-233)."""
    for py_file in _py_files(DECODEBOT_DIR):
        if _is_within(py_file, RECOMMENDER_DIR):
            continue
        for module in _imported_modules(py_file):
            if _matches(module, "decodebot.recommender"):
                if os.path.basename(py_file) not in _WIRING_FILES:
                    pytest.fail(
                        f"decodebot.recommender imported in {py_file}; only "
                        "wiring files may bridge to the recommender package "
                        "(FR-233)."
                    )


@pytest.mark.parametrize("py_file", _py_files(RECOMMENDER_DIR))
def test_no_module_scope_ml_imports_in_recommender(py_file):
    """Recommender modules may not import ML libs at module scope (FR-234)."""
    for module in _top_level_imported_modules(py_file):
        for library in ML_LIBRARIES:
            assert not _matches(
                module, library
            ), f"{module} imported at module scope in {py_file} (FR-234)"


@pytest.mark.parametrize("py_file", _py_files(RECOMMENDER_DIR))
def test_no_other_subsystem_imports_in_recommender(py_file):
    """Recommender must not import decodebot.ml/decodebot.core (FR-233)."""
    for module in _imported_modules(py_file):
        for subsystem in OTHER_SUBSYSTEMS:
            assert not _matches(module, subsystem), f"{module} imported in {py_file} (FR-233)"


def test_importing_recommender_is_lazy_and_side_effect_free():
    """Importing the package pulls no heavy/sibling modules and no data."""
    script = (
        "import sys\n"
        "import decodebot.recommender as recommender\n"
        "import decodebot.recommender.corpus as corpus\n"
        "present = [m for m in ("
        "'sklearn', 'pandas', 'numpy', 'matplotlib', 'joblib', 'tkinter', "
        "'decodebot.ml', 'decodebot.core') if m in sys.modules]\n"
        "if present:\n"
        "    print('PRESENT:' + ','.join(present))\n"
        "    sys.exit(1)\n"
        "if corpus._CACHE:\n"
        "    print('CACHE-NOT-EMPTY')\n"
        "    sys.exit(1)\n"
        "print('OK')\n"
    )
    result = _run_subprocess(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_engine_startup_does_not_import_recommender():
    """decodebot.core.app starts without touching recommender (FR-234)."""
    script = (
        "import sys\n"
        "import decodebot.core.app\n"
        "for m in sys.modules:\n"
        "    if m == 'decodebot.recommender' "
        "or m.startswith('decodebot.recommender.'):\n"
        "        print('IMPORTED:' + m)\n"
        "        sys.exit(1)\n"
        "print('OK')\n"
    )
    result = _run_subprocess(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_recommender_modules_are_discoverable():
    """W3-M1 recommender module set exists on disk."""
    for module_name in ("__init__", "corpus"):
        assert os.path.isfile(
            os.path.join(RECOMMENDER_DIR, module_name + ".py")
        ), f"decodebot/recommender/{module_name}.py is missing"
