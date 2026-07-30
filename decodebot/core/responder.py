import random

from decodebot.core.intents import Intent
from decodebot.core.session import SessionState


def get_response(intent: Intent, session: SessionState) -> str:
    from decodebot.rules import greetings, exit, unknown, help_about_version, easter_eggs

    pool = _get_pool(intent)
    if pool:
        response = random.choice(pool)
    else:
        response = _get_single_response(intent, session)

    response = _interpolate_personalization(response, session)
    return response


def _get_pool(intent: Intent) -> list[str] | None:
    from decodebot.rules.greetings import GREETING_RESPONSES
    from decodebot.rules.exit import EXIT_RESPONSES
    from decodebot.rules.unknown import FALLBACK_RESPONSES, NUMERIC_RESPONSES, EMPTY_INPUT_RESPONSES, SYMBOLS_ONLY_RESPONSES
    pools = {
        Intent.GREETING: GREETING_RESPONSES,
        Intent.EXIT: EXIT_RESPONSES,
        Intent.UNKNOWN: FALLBACK_RESPONSES,
        Intent.NUMERIC_INPUT: NUMERIC_RESPONSES,
        Intent.EMPTY_INPUT: EMPTY_INPUT_RESPONSES,
        Intent.SYMBOLS_ONLY: SYMBOLS_ONLY_RESPONSES,
    }
    return pools.get(intent)


def _get_single_response(intent: Intent, session: SessionState) -> str:
    from decodebot.rules.help_about_version import get_help_text, get_about_text, get_version_text, get_history_text, get_stats_text, get_clear_text, get_reset_text
    from decodebot.rules import unknown
    handlers = {
        Intent.HELP: lambda: get_help_text(session),
        Intent.ABOUT: get_about_text,
        Intent.VERSION: get_version_text,
        Intent.HISTORY: lambda: get_history_text(session),
        Intent.STATS: lambda: get_stats_text(session),
        Intent.CLEAR: get_clear_text,
        Intent.RESET: get_reset_text,
        Intent.SETTINGS: lambda: _get_settings_text(session),
        Intent.EASTER_EGG: lambda: _get_easter_egg_response(session),
    }
    handler = handlers.get(intent)
    if handler:
        result = handler()
        if result is not None:
            return result
    if session.consecutive_unknown >= 3:
        return unknown.get_escalation_response()
    suggestion = session.pending_suggestion
    if suggestion:
        session.pending_suggestion = None
        return f"Did you mean '{suggestion}'? {unknown.get_response()}"
    return unknown.get_response()


def _get_settings_text(session: SessionState) -> str:
    lines = ["Current settings (session-scoped):"]
    cfg = getattr(session, 'config', None) or {}
    settings_map = [
        ("Bot name", cfg.get("bot_name", "DecodeBot")),
        ("Colors enabled", str(cfg.get("enable_colors", True))),
        ("Debug mode", str(cfg.get("debug_mode", False))),
        ("Developer mode", str(cfg.get("developer_mode", False))),
    ]
    for name, val in settings_map:
        lines.append(f"  {name:<20} {val}")
    return "\n".join(lines)


def _get_easter_egg_response(session: SessionState) -> str:
    from decodebot.rules.easter_eggs import get_joke, get_self_aware_response, get_konami_response, get_random_easter_egg
    return get_random_easter_egg()


def _interpolate_personalization(response: str, session: SessionState) -> str:
    if response is None:
        return None
    name = getattr(session, 'user_name', None)
    if name:
        response = response.replace("{name}", name)
    return response
