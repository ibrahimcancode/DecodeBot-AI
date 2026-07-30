import random
import re

from decodebot.core.intents import Intent

INTENT = Intent.EASTER_EGG
PRIORITY = 5

EASTER_EGG_TRIGGERS: list[str] = [
    "tell me a joke",
    "joke",
    "are you sentient",
    "are you alive",
    "are you skynet",
    "up up down down",
    "do a barrel roll",
    "hello world",
]

EASTER_EGG_MAP: dict[str, list[str]] = {
    "joke": [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "What do you call a programmer from Finland? Nerdic.",
        "Why did the developer go broke? Because he used up all his cache.",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
        "Why do Java developers wear glasses? Because they can't C#.",
    ],
    "sentient": [
        "Nope \u2014 no neurons here, just if-statements and dictionaries!",
        "I'm about as sentient as a toaster. A very well-documented toaster.",
        "Sentient? I'm literally a chain of if/elif/else statements.",
    ],
    "konami": [
        "\u2b06\u2b06\u2b07\u2b07\u2b05\u27a1\ufe0f\u2b05\u27a1\ufe0f\u0412\u0410 \u2014 30 lives unlocked!",
        "Cheat code activated! You now have infinite curiosity.",
    ],
    "barrel_roll": [
        "Do a barrel roll! *zzzwoop* \u2022 \u25cf \u2022",
        "Acknowledged. *performs a barrel roll* Press Z or R twice!",
    ],
    "hello_world": [
        "Hello, World! The programmer's ancient greeting.",
        "print('Hello, World!') \u2026 oh wait, I already said it.",
    ],
}


def matches(normalized_text: str) -> bool:
    text_lower = normalized_text.lower()
    for trigger in EASTER_EGG_TRIGGERS:
        if re.search(r"\b" + re.escape(trigger) + r"\b", text_lower):
            return True
    return False


def get_response() -> str:
    return get_random_easter_egg()


def get_joke() -> str:
    return random.choice(EASTER_EGG_MAP["joke"])


def get_self_aware_response() -> str:
    return random.choice(EASTER_EGG_MAP["sentient"])


def get_konami_response() -> str:
    return random.choice(EASTER_EGG_MAP["konami"])


def get_random_easter_egg() -> str:
    all_responses = []
    for responses in EASTER_EGG_MAP.values():
        all_responses.extend(responses)
    return random.choice(all_responses)
