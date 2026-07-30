from decodebot.core.session import SessionState


def get_history_text(session: SessionState) -> str:
    if not session.history:
        return "No conversation yet!"
    lines = []
    for i, (raw_inp, intent, resp) in enumerate(session.history, 1):
        intent_name = intent.name if hasattr(intent, 'name') else str(intent)
        lines.append(f"#{i} You: {raw_inp} \u2192 Bot: {resp}")
    return "\n".join(lines)
