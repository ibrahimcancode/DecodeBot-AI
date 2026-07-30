"""Unknown / fallback intent rule module (FR-046–FR-053).

Provides fallback response pool, escalating fallback for
consecutive unknown inputs, and fuzzy suggestion stubs.
"""

import random

from decodebot.core.intents import Intent

INTENT = Intent.UNKNOWN
PRIORITY = 100

FALLBACK_RESPONSES: list[str] = [
    "Hmm, I didn't quite catch that. Try 'help' for a list of things I understand.",
    "I'm not sure what you mean. Try typing 'help' to see what I can do.",
    "That's outside what I know how to answer. Type 'help' for guidance.",
    "I didn't quite get that. Could you rephrase?",
    "Not sure I follow. Try 'help' to see everything I can do!",
    "I'm not programmed to handle that. 'help' might show you something useful.",
    "Sorry, I don't understand that. Try asking in a different way.",
    "Hmm, that stumped me. 'help' will show you what I know.",
]

ESCALATION_RESPONSE: str = (
    "I'm having trouble understanding a few messages in a row "
    "— type 'help' to see everything I can do!"
)

NUMERIC_RESPONSES: list[str] = [
    "That's a number! I'm rule-based, so I can't do math, but I noticed you typed a number.",
    "I see a number there — unfortunately I can't calculate anything, I'm just a chatbot.",
    "Numbers! I wish I could compute, but I'm strictly a rule-based bot.",
]

EMPTY_INPUT_RESPONSES: list[str] = [
    "I didn't catch that — could you type something?",
    "Empty message! Try saying something.",
    "I didn't hear anything — type a message when you're ready.",
    "Go ahead, type something! I'm listening.",
]

SYMBOLS_ONLY_RESPONSES: list[str] = [
    "That looks like symbols, not words — try typing 'help'.",
    "I don't recognize those symbols. Try using words!",
    "Symbols aren't something I understand. Type 'help' to see what works.",
]

TOPIC_FALLBACKS: dict[str, list[str]] = {
    "weather": [
        "I don't have access to real-world data like weather — I'm a rule-based bot!",
        "Weather is outside my abilities — I'm a rule-based chatbot, not a forecast service.",
    ],
    "sports": [
        "I don't follow sports — I'm a rule-based bot, not a sports commentator!",
        "Sports aren't in my wheelhouse. Try 'help' to see what I *can* do.",
    ],
    "music": [
        "I don't know much about music — I'm just a rule-based chatbot!",
        "Music isn't my area. Type 'help' to see what I understand.",
    ],
}

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "weather": ["weather", "rain", "temperature", "forecast", "sunny", "cloudy", "storm"],
    "sports": ["sports", "game", "team", "score", "match", "player", "football", "basketball", "soccer"],
    "music": ["music", "song", "band", "album", "artist", "playlist", "melody"],
}


def matches(normalized_text: str) -> bool:
    """Unknown always matches as the lowest-priority fallback."""
    return True


def get_response() -> str:
    """Return a randomly selected fallback response (FR-047)."""
    return random.choice(FALLBACK_RESPONSES)


def get_escalation_response() -> str:
    """Return the escalating fallback message (FR-048)."""
    return ESCALATION_RESPONSE


def get_numeric_response() -> str:
    """Return a numeric-input response (FR-019)."""
    return random.choice(NUMERIC_RESPONSES)


def get_empty_input_response() -> str:
    """Return an empty-input response (FR-021)."""
    return random.choice(EMPTY_INPUT_RESPONSES)


def get_symbols_only_response() -> str:
    """Return a symbols-only response (FR-020)."""
    return random.choice(SYMBOLS_ONLY_RESPONSES)


def topic_fallback(normalized_text: str) -> str | None:
    """Check for known topic keywords and return a topic-specific
    fallback if found (FR-051).

    Args:
        normalized_text: The normalized user input.

    Returns:
        A topic-specific response string, or None if no topic
        keyword is recognized.
    """
    for topic, keywords in _TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in normalized_text:
                return random.choice(TOPIC_FALLBACKS[topic])
    return None
