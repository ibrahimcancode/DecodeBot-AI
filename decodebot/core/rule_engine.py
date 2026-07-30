import re

from decodebot.core.intents import Intent
from decodebot.core.session import SessionState
from decodebot.utils.normalization import (
    normalize,
    is_numeric_only,
    is_symbols_only,
)
from decodebot import rules as rules_pkg
from decodebot.rules import greetings, exit, unknown, easter_eggs
from decodebot.rules.help_about_version import COMMANDS, ALIASES, HIDDEN_COMMANDS

ALL_RULES = [greetings, exit, unknown, easter_eggs]

COMMAND_KEYWORDS: list[str] = list(COMMANDS.keys())

EXTRA_COMMAND_TRIGGERS: dict[str, Intent] = {
    "what can you do": Intent.HELP,
    "who are you": Intent.ABOUT,
    "what are you": Intent.ABOUT,
}


def _light_normalize(text: str) -> str:
    return text.strip().lower()


def _classify_command(normalized: str) -> Intent | None:
    if normalized in COMMANDS:
        return COMMANDS[normalized][1]
    if normalized in ALIASES:
        canonical = ALIASES[normalized]
        if canonical in COMMANDS:
            return COMMANDS[canonical][1]
    if normalized in EXTRA_COMMAND_TRIGGERS:
        return EXTRA_COMMAND_TRIGGERS[normalized]
    for alias, canonical in ALIASES.items():
        if alias == normalized:
            if canonical in COMMANDS:
                return COMMANDS[canonical][1]
    for cmd in COMMANDS:
        if re.search(r"\b" + re.escape(cmd) + r"\b", normalized):
            return COMMANDS[cmd][1]
    for alias, canonical in ALIASES.items():
        if len(alias) > 2 and re.search(r"\b" + re.escape(alias) + r"\b", normalized):
            if canonical in COMMANDS:
                return COMMANDS[canonical][1]
    return None


def classify_intent(raw_input: str, session: SessionState) -> Intent:
    light = _light_normalize(raw_input)

    if light == "":
        return Intent.EMPTY_INPUT

    from decodebot.rules.personalization import is_forget_request, extract_name, NAME_PATTERNS
    if is_forget_request(light):
        session.pending_suggestion = None
        session.user_name = None
        return Intent.SETTINGS

    for pattern in ["set name ", "call me "]:
        if light.startswith(pattern):
            name = light[len(pattern):].strip()
            if name:
                from decodebot.rules.personalization import sanitize_name
                clean = sanitize_name(name)
                if clean:
                    session.user_name = clean
                    session.pending_text = f"Got it, I'll call you {clean}!"
                    session.pending_suggestion = None
                    return Intent.SETTINGS

    cmd_intent = _classify_command(light)
    if cmd_intent is not None:
        session.pending_suggestion = None
        return cmd_intent

    if is_numeric_only(light):
        return Intent.NUMERIC_INPUT

    if is_symbols_only(light):
        return Intent.SYMBOLS_ONLY

    normalized = normalize(raw_input)

    if normalized == "":
        return Intent.EMPTY_INPUT

    cmd_intent = _classify_command(normalized)
    if cmd_intent is not None:
        session.pending_suggestion = None
        return cmd_intent

    from decodebot.rules.personalization import extract_name
    extracted = extract_name(normalized)
    if extracted:
        session.user_name = extracted

    candidates = []
    for rule in sorted(ALL_RULES, key=lambda r: r.PRIORITY):
        if rule.matches(normalized):
            candidates.append(rule)

    if candidates:
        winning_rule = candidates[0]
        session.pending_suggestion = None
        return winning_rule.INTENT

    return Intent.UNKNOWN
