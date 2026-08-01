import os
import time
import logging

from decodebot import __version__
from decodebot.core.config import load_config
from decodebot.core.dispatcher import dispatch
from decodebot.core.io_handler import get_input, print_response
from decodebot.core.session import SessionState
from decodebot.core.intents import Intent
from decodebot.utils.animations import animated_print, show_thinking

BANNER = f"""
+==========================================+
|         D E C O D E B O T   A I         |
|   Rule-Based Conversational Agent        |
|              v{__version__}                      |
+==========================================+
"""

PROMPT = "You: "


def run_session() -> int:
    config = load_config()
    session = SessionState()
    session.start_time = time.monotonic()
    session.config = config
    anim_enabled = config.get("enable_animations", True)
    reduced = config.get("reduced_motion", False)
    tw_speed = config.get("typewriter_speed", 0.015)
    _print_banner()

    consecutive_errors = 0

    while True:
        try:
            raw = get_input(prompt=PROMPT)
        except KeyboardInterrupt:
            _print_farewell(session, "interrupt")
            return 0
        except EOFError:
            _print_farewell(session, "eof")
            return 0

        try:
            session.last_input = raw
            intent = dispatch_intent(raw, session)
            if intent == Intent.EXIT:
                _print_farewell(session, "command")
                return 0

            if intent == Intent.CLEAR:
                _clear_screen()
                _print_banner()
                session.record_turn(raw, intent, "[screen cleared]")
                consecutive_errors = 0
                continue

            if intent == Intent.RESET:
                session.reset()
                session.start_time = time.monotonic()
                from decodebot.rules.help_about_version import get_reset_text

                resp = get_reset_text()
                animated_print(f"Bot: {resp}", enabled=anim_enabled, speed=tw_speed)
                session.record_turn(raw, intent, resp)
                consecutive_errors = 0
                continue

            thinking_done = show_thinking(enabled=anim_enabled, reduced=reduced)
            response_text = dispatch(intent, session)
            thinking_done.set()
            animated_print(f"Bot: {response_text}", enabled=anim_enabled, speed=tw_speed)
            session.record_turn(raw, intent, response_text)
            consecutive_errors = 0

        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("Unhandled error in loop")
            print_response(
                "Bot: Oops, something went wrong on my end "
                "\u2014 but I'm still here. Let's keep going!"
            )
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print_response(
                    "Bot: Too many errors. I need to stop now. " "Check the logs for details."
                )
                return 1


def dispatch_intent(raw_input: str, session: SessionState) -> Intent:
    from decodebot.core.rule_engine import classify_intent

    return classify_intent(raw_input, session)


def _print_banner() -> None:
    print_response(BANNER.strip())
    print_response("Type 'help' to see what I can do.")
    print_response("")


def _print_farewell(session: SessionState, reason: str) -> None:
    if reason == "interrupt":
        print_response("\nBot: Session interrupted. Goodbye!")
    elif reason == "eof":
        print_response("\nBot: Input stream ended. Goodbye!")
    else:
        summary = _build_summary(session)
        if summary:
            print_response(f"Bot: {summary}")
        print_response(f"Bot: {dispatch(Intent.EXIT, session)}")


def _build_summary(session: SessionState) -> str | None:
    if session.message_count == 0:
        return "We didn't get to chat much \u2014 see you next time!"
    from decodebot.core.stats import get_session_duration

    dur = get_session_duration(session)
    return f"We exchanged {session.message_count} messages over {dur}. Thanks for chatting!"


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")
