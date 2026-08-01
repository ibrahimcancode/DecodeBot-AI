from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionState:
    history: list[tuple[str, Any, str]] = field(default_factory=list)
    consecutive_unknown: int = 0
    first_greeting_seen: bool = False
    pending_suggestion: str | None = None
    message_count: int = 0
    user_name: str | None = None
    intent_counts: dict[str, int] = field(default_factory=dict)
    start_time: float | None = None
    pending_text: str | None = None
    last_input: str = ""
    ml_state: dict[str, object] = field(default_factory=dict)

    def record_turn(self, raw_input: str, intent: Any, response: str) -> None:
        from decodebot.core.intents import Intent

        self.history.append((raw_input, intent, response))
        if len(self.history) > 100:
            self.history.pop(0)

        if intent == Intent.UNKNOWN:
            self.consecutive_unknown += 1
        else:
            self.consecutive_unknown = 0

        if intent != Intent.EMPTY_INPUT:
            self.message_count += 1

        if intent == Intent.GREETING and not self.first_greeting_seen:
            self.first_greeting_seen = True

        intent_name = intent.name if hasattr(intent, "name") else str(intent)
        if intent_name:
            self.intent_counts[intent_name] = self.intent_counts.get(intent_name, 0) + 1

    def reset(self) -> None:
        self.history.clear()
        self.consecutive_unknown = 0
        self.first_greeting_seen = False
        self.pending_suggestion = None
        self.message_count = 0
        self.user_name = None
        self.intent_counts.clear()
        self.pending_text = None
        self.last_input = ""
        self.ml_state.clear()
