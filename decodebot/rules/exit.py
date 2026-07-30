"""Exit / farewell intent rule module (FR-036–FR-045).

Provides pattern table, negation exclusion list, and response
pool for EXIT classification.
"""

import re
import random

from decodebot.core.intents import Intent

INTENT = Intent.EXIT
PRIORITY = 10

EXIT_PATTERNS: list[str] = [
    "bye",
    "exit",
    "quit",
    "goodbye",
    "see you",
    "later",
    "stop",
    "end",
    "close",
    "q",
]

EXIT_NEGATION_PATTERNS: list[str] = [
    "don't go",
    "dont go",
    "never leaving",
    "don't quit",
    "dont quit",
    "stay",
]

EXIT_RESPONSES: list[str] = [
    "Goodbye! Have a great day.",
    "See you next time!",
    "Bye! Thanks for chatting.",
    "Take care! Come back anytime.",
    "Later! It was nice talking to you.",
    "Catch you later!",
]


def matches(normalized_text: str) -> bool:
    """Check if normalized text is an exit command (FR-037).

    Uses word-boundary matching and checks negation
    exclusion list (FR-042) before returning True.

    Single-character alias 'q' must be the entire
    normalized input (FR-044).
    """
    text_lower = normalized_text.lower()

    for neg in EXIT_NEGATION_PATTERNS:
        if re.search(r"\b" + re.escape(neg) + r"\b", text_lower):
            return False

    for pattern in EXIT_PATTERNS:
        if len(pattern) == 1:
            if text_lower == pattern:
                return True
            continue
        if re.search(r"\b" + re.escape(pattern) + r"\b", text_lower):
            return True
    return False


def get_response() -> str:
    """Return a randomly selected farewell response (FR-039)."""
    return random.choice(EXIT_RESPONSES)
