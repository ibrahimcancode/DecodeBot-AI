import re
import unicodedata


def normalize(raw_input: str) -> str:
    """Normalize raw user input for rule matching.

    Applies, in order: leading/trailing whitespace strip (FR-013),
    lowercase (FR-014), internal whitespace collapse (FR-016),
    trailing/leading punctuation strip (FR-015), and control
    character removal (FR-024).

    Args:
        raw_input: The unmodified string captured from the user.

    Returns:
        The normalized string, ready for rule matching.
    """
    text = raw_input.strip()
    text = text.lower()
    text = _collapse_whitespace(text)
    text = _strip_trailing_leading_punctuation(text)
    text = _strip_control_characters(text)
    return text


def _collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace into a single space."""
    return re.sub(r'\s+', ' ', text)


def _strip_trailing_leading_punctuation(text: str) -> str:
    """Strip common trailing/leading punctuation characters.

    Internal punctuation (e.g. apostrophes in contractions) is
    preserved.
    """
    punct = r'[.,!?;:\'"()\[\]{}<>@#$%^&*_~`+=|\\/]'
    text = re.sub(r'^' + punct + r'+', '', text)
    text = re.sub(punct + r'+$', '', text)
    return text


def _strip_control_characters(text: str) -> str:
    """Remove control characters (including \\r, \\n, \\x00)."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)


def is_numeric_only(text: str) -> bool:
    """Return True if the normalized text is purely numeric.

    Handles negative numbers, decimals, and comma-separated
    thousands (FR-019).
    """
    if not text:
        return False
    cleaned = text.replace(',', '').replace('.', '')
    if cleaned.startswith('-'):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and len(cleaned) > 0


def is_symbols_only(text: str) -> bool:
    """Return True if the normalized text contains only symbols.

    Symbols are defined as non-alphanumeric, non-whitespace
    characters (FR-020).
    """
    if not text:
        return False
    for ch in text:
        if ch.isalnum() or ch.isspace():
            return False
    return True


def is_whitespace_only(text: str) -> bool:
    """Return True if the raw text is entirely whitespace."""
    return text.strip() == ''
