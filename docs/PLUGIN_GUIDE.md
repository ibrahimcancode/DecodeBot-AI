# Plugin Guide

DecodeBot AI supports auto-discovered rule modules.

## Interface

Each plugin module must expose:

- `PATTERNS: list[str]` — trigger phrases
- `INTENT: Intent` — the intent enum value
- `RESPONSES: list[str]` — response pool
- `PRIORITY: int` (optional, default 100) — match priority (lower = higher)
- `matches(normalized_text: str) -> bool` — matching function

## Example

```python
from decodebot.core.intents import Intent

PATTERNS = ["thanks", "thank you", "ty"]
INTENT = Intent.EASTER_EGG
RESPONSES = ["You're welcome!", "Anytime!", "Glad to help!"]
PRIORITY = 50

def matches(normalized_text: str) -> bool:
    import re
    for p in PATTERNS:
        if re.search(r"\b" + re.escape(p) + r"\b", normalized_text):
            return True
    return False
```

## Constraints

- No network calls
- No file writes outside designated directories
- No ML/NLP/LLM dependencies
- Pure rule-based logic only
