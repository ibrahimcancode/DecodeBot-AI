"""Injectable I/O boundary (FR-011, FR-012, FR-022).

Thin wrappers around input() and print() so they can be
replaced with mocks in automated tests.
"""

import sys


def get_input(prompt: str = "") -> str:
    """Read a line of user input.

    Args:
        prompt: The prompt string displayed before input.

    Returns:
        The raw input string as typed by the user.
    """
    return input(prompt)


def print_response(text: str, end: str = "\n") -> None:
    """Print a response to the user.

    Args:
        text: The response text to display.
        end: String appended after the text (default newline).
    """
    print(text, end=end)
    sys.stdout.flush()
