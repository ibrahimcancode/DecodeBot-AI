"""Greeting intent rule module (FR-026–FR-035).

Provides pattern table and response pool for GREETING classification.
"""

import re
import random

from decodebot.core.intents import Intent

INTENT = Intent.GREETING
PRIORITY = 10

GREETING_PATTERNS: list[str] = [
    "hi",
    "hello",
    "hey",
    "yo",
    "good morning",
    "good afternoon",
    "good evening",
    "greetings",
    "howdy",
    "sup",
    "what's up",
    "hiya",
    "heya",
    "hey there",
    "howdy do",
]

GREETING_RESPONSES: list[str] = [
    "Hello! I'm DecodeBot — how can I help you today?",
    "Hey there! What's on your mind?",
    "Hi! Great to see you.",
    "Hey! How's it going?",
    "Hello! What can I do for you?",
    "Yo! What's happening?",
    "Hi there! Ready to chat?",
    "Hey! I'm all ears.",
]

WELCOME_RESPONSE: str = (
    "Hi! Welcome — I'm DecodeBot. Type 'help' anytime to see what I can do."
)


def matches(normalized_text: str) -> bool:
    """Check if normalized text is a greeting.

    Supports exact match (FR-027) and word-boundary-aware
    substring match (FR-028, FR-033).
    """
    if normalized_text in GREETING_PATTERNS:
        return True
    for pattern in GREETING_PATTERNS:
        if re.search(r"\b" + re.escape(pattern) + r"\b", normalized_text):
            return True
    return False


def get_response(is_first_greeting: bool = False) -> str:
    """Return a randomly selected greeting response (FR-029).

    Args:
        is_first_greeting: If True, returns the extended
            welcome variant instead (FR-031).

    Returns:
        A greeting response string.
    """
    if is_first_greeting:
        return WELCOME_RESPONSE
    return random.choice(GREETING_RESPONSES)
