from decodebot.core.intents import Intent

COMMANDS: dict[str, tuple[str, Intent]] = {
    "help": ("Show this help message", Intent.HELP),
    "about": ("Learn about DecodeBot", Intent.ABOUT),
    "version": ("Show the current version", Intent.VERSION),
    "history": ("View this session's chat log", Intent.HISTORY),
    "stats": ("View session statistics", Intent.STATS),
    "settings": ("View/change runtime settings", Intent.SETTINGS),
    "reset": ("Clear session state", Intent.RESET),
    "clear": ("Clear the screen", Intent.CLEAR),
    "bye": ("Exit DecodeBot", Intent.EXIT),
}

ALIASES: dict[str, str] = {
    "?": "help",
    "commands": "help",
    "what can you do": "help",
    "info": "about",
    "who are you": "about",
    "what are you": "about",
    "v": "version",
    "--version": "version",
    "cls": "clear",
    "log": "history",
    "statistics": "stats",
    "restart": "reset",
}

HIDDEN_COMMANDS: dict[str, str] = {}

PRIORITY = 10
INTENT = Intent.HELP

HELP_RESPONSES: list[str] = []
ABOUT_RESPONSES: list[str] = []
VERSION_RESPONSES: list[str] = []


def get_help_text(session=None) -> str:
    from decodebot import __version__
    header = "I understand these commands:\n"
    items = []
    for cmd in sorted(COMMANDS):
        desc = COMMANDS[cmd][0]
        items.append(f"  {cmd:<10} {desc}")
    body = "\n".join(items)
    footer = f"\n\nDecodeBot AI v{__version__} — type a command to get started!"
    if session and getattr(session, "user_name", None):
        footer = f"\n\nType a command anytime, {session.user_name}!"
    return header + body + footer


def get_about_text() -> str:
    from decodebot import __version__
    return (
        f"DecodeBot AI v{__version__}\n"
        "A 100% rule-based conversational agent.\n"
        "Built with pure Python, zero AI/ML/NLP dependencies.\n"
        "Type 'help' to see what I can do."
    )


def get_version_text() -> str:
    from decodebot import __version__
    return f"DecodeBot AI version {__version__}"


def get_history_text(session) -> str:
    if not session or not session.history:
        return "No conversation yet!"
    lines = []
    for i, (raw_inp, intent, resp) in enumerate(session.history, 1):
        lines.append(f"#{i} You: {raw_inp} \u2192 Bot: {resp}")
    return "\n".join(lines)


def get_stats_text(session) -> str:
    if not session:
        return "No session data available."
    lines = []
    lines.append(f"Messages: {session.message_count}")
    if session.intent_counts:
        lines.append("Intent breakdown:")
        for intent_name, count in sorted(session.intent_counts.items()):
            lines.append(f"  {intent_name}: {count}")
    from decodebot.core.stats import get_session_duration
    dur = get_session_duration(session)
    lines.append(f"Session duration: {dur}")
    lines.append(f"Unknown count: {session.intent_counts.get('UNKNOWN', 0)}")
    return "\n".join(lines)


def get_clear_text() -> str:
    return None


def get_reset_text() -> str:
    return "Session reset! Starting fresh."


def get_settings_text(session) -> str:
    lines = []
    lines.append("Runtime settings:")
    lines.append("  1. Colors: ON" if getattr(session, 'config', None) and session.config.get('enable_colors', True) else "  1. Colors: OFF")
    return "\n".join(lines)


def matches(normalized_text: str) -> bool:
    return False
