import re

from decodebot.core.intents import Intent

INTENT = None
PRIORITY = 5

NAME_PATTERNS: list[str] = [
    "my name is ",
    "i'm ",
    "i am ",
    "call me ",
    "set name ",
]

FORGET_PATTERNS: list[str] = [
    "forget my name",
    "forget me",
]


def extract_name(normalized_text: str) -> str | None:
    text_lower = normalized_text.lower()
    for pattern in NAME_PATTERNS:
        if text_lower.startswith(pattern):
            name = normalized_text[len(pattern):].strip()
            return sanitize_name(name)
    return None


def is_forget_request(normalized_text: str) -> bool:
    text_lower = normalized_text.lower()
    for pattern in FORGET_PATTERNS:
        if re.search(r"\b" + re.escape(pattern) + r"\b", text_lower):
            return True
    return False


def sanitize_name(name: str) -> str | None:
    if not name or not name.strip():
        return None
    cleaned = re.sub(r'[^a-zA-Z\s\-\']', '', name)
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    if len(cleaned) > 30:
        cleaned = cleaned[:30].rstrip()
    if not cleaned:
        return None
    return cleaned


def matches(normalized_text: str) -> bool:
    return False
