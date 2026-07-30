"""Static scan gate — verify zero prohibited imports (FR-009, TC-A-002).

Scans all Python files in the project for prohibited
ML/DL/NLP/LLM packages. Fails the build if any are found.
"""

import ast
import os
import pytest

PROHIBITED_IMPORTS: list[str] = [
    "spacy",
    "nltk",
    "transformers",
    "torch",
    "tensorflow",
    "langchain",
    "rasa",
    "openai",
    "anthropic",
    "google.generativeai",
    "huggingface",
    "sentence_transformers",
    "sklearn",
    "keras",
    "jax",
    "pytorch_lightning",
    "gensim",
    "fastai",
    "flair",
    "stanza",
    "allennlp",
]

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _get_py_files() -> list[str]:
    """Return all .py files under the project root, excluding
    hidden directories and venv."""
    py_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "env", ".venv")]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


@pytest.mark.parametrize("py_file", _get_py_files())
def test_no_prohibited_imports(py_file: str) -> None:
    """Verify that py_file contains no prohibited imports."""
    with open(py_file, encoding="utf-8", errors="replace") as f:
        try:
            tree = ast.parse(f.read(), filename=py_file)
        except SyntaxError:
            pytest.fail(f"Syntax error in {py_file}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _check_alias(alias.name, py_file)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _check_alias(node.module, py_file)


def _check_alias(module_name: str, py_file: str) -> None:
    """Fail the test if module_name is in the prohibited list."""
    for prohibited in PROHIBITED_IMPORTS:
        if module_name == prohibited or module_name.startswith(prohibited + "."):
            pytest.fail(
                f"Prohibited import '{module_name}' found in {py_file}"
            )
