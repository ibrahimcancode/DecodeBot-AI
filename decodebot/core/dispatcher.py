from decodebot.core.intents import Intent
from decodebot.core.session import SessionState
from decodebot.core.responder import get_response
from decodebot.rules import greetings, exit, unknown
from decodebot.rules.help_about_version import COMMANDS


def dispatch(intent: Intent, session: SessionState) -> str:
    if intent == Intent.GREETING:
        is_first = not session.first_greeting_seen
        return greetings.get_response(is_first_greeting=is_first)

    elif intent == Intent.EXIT:
        return exit.get_response()

    elif intent == Intent.HELP:
        return get_response(intent, session)

    elif intent == Intent.ABOUT:
        return get_response(intent, session)

    elif intent == Intent.VERSION:
        return get_response(intent, session)

    elif intent == Intent.HISTORY:
        return get_response(intent, session)

    elif intent == Intent.STATS:
        return get_response(intent, session)

    elif intent == Intent.SETTINGS:
        if session.pending_text:
            text = session.pending_text
            session.pending_text = None
            return text
        return get_response(intent, session)

    elif intent == Intent.RESET:
        return get_response(intent, session)

    elif intent == Intent.CLEAR:
        return get_response(intent, session)

    elif intent == Intent.EASTER_EGG:
        return get_response(intent, session)

    elif intent == Intent.EMPTY_INPUT:
        return unknown.get_empty_input_response()

    elif intent == Intent.NUMERIC_INPUT:
        return unknown.get_numeric_response()

    elif intent == Intent.SYMBOLS_ONLY:
        return unknown.get_symbols_only_response()

    else:
        if session.consecutive_unknown >= 3:
            return unknown.get_escalation_response()
        suggestion = session.pending_suggestion
        if suggestion:
            session.pending_suggestion = None
            return f"Did you mean '{suggestion}'? {unknown.get_response()}"
        return unknown.get_response()
