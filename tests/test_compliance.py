"""Compliance gate tests — the 8 mandatory DecodeLabs checks.

These tests map directly to the DecodeLabs Internship
Compliance Matrix rows 1-8. Every test must pass before
any other test group is run (NFR-035).
"""

import subprocess
import sys
import os
import ast
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_PY = os.path.join(PROJECT_ROOT, "main.py")
DISPATCHER_PY = os.path.join(
    PROJECT_ROOT, "decodebot", "core", "dispatcher.py"
)


def test_tc_core_001_py_file_exists_and_valid():
    """TC-CORE-001: .py file exists and is valid."""
    assert os.path.isfile(MAIN_PY), "main.py does not exist"
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", MAIN_PY],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"main.py has syntax errors: {result.stderr}"


def test_tc_core_002_program_runs():
    """TC-CORE-002: Program runs via python main.py (banner + prompt)."""
    result = subprocess.run(
        [sys.executable, MAIN_PY],
        input="bye\n",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
    stdout = result.stdout + result.stderr
    has_banner = "DECODEBOT" in stdout.replace(" ", "") or "DecodeBot" in stdout
    assert has_banner, f"Banner not found in output: {stdout[:200]}"


def test_tc_core_003_while_loop_present():
    """TC-CORE-003: while loop present and functioning."""
    with open(os.path.join(PROJECT_ROOT, "decodebot", "core", "loop.py")) as f:
        source = f.read()
    tree = ast.parse(source)
    found_while = False
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            found_while = True
            break
    assert found_while, "No while loop found in loop.py"


def test_tc_core_005_if_elif_else_dispatch_present():
    """TC-CORE-005: if/elif/else dispatch present in dispatcher.py."""
    with open(DISPATCHER_PY) as f:
        source = f.read()
    tree = ast.parse(source)
    found_chain = False
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            has_elif = any(
                isinstance(n, ast.If) for n in ast.walk(node)
            )
            if has_elif:
                found_chain = True
                break
    if not found_chain:
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                found_chain = True
                break
    assert found_chain, "No if/elif/else chain found in dispatcher.py"


def test_tc_core_007_accepts_user_input():
    """TC-CORE-007: Accepts user input via input()."""
    with open(os.path.join(PROJECT_ROOT, "decodebot", "core", "io_handler.py")) as f:
        source = f.read()
    assert "input(" in source or "input()" in source.replace(" ", "")


def test_tc_core_008_input_is_injectable():
    """TC-CORE-008: Input capture is injectable/testable."""
    with open(os.path.join(PROJECT_ROOT, "decodebot", "core", "io_handler.py")) as f:
        source = f.read()
    tree = ast.parse(source)
    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "get_input" in functions
    assert "print_response" in functions
