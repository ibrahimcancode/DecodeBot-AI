# DecodeBot AI

A 100% rule-based conversational agent built in pure Python — no ML, no NLP, no LLMs. Every reply comes from an explicit, human-readable rule.

## Why Rule-Based?

Rule-based AI is transparent, predictable, and fully auditable. Every response can be traced to a specific pattern and handler. There's no black box, no statistical uncertainty, and no external API calls. This project demonstrates that useful conversational agents can be built with nothing but Python's standard library and careful engineering.

## Features

- Greeting, exit, and fallback handling with varied response pools
- Help, About, Version commands with aliases
- Session conversation history (bounded to 100 turns)
- Runtime statistics (message count, duration, intent breakdown)
- Personalization (set/forget your name)
- Hidden easter eggs and commands
- Configurable settings (bot name, colors, debug mode, animations)
- Rotating file logging with configurable levels
- Plugin auto-discovery system for extending rules
- CLI animations (typewriter effect, thinking indicator)
- Fuzzy command suggestion via Levenshtein distance

## Installation

```bash
git clone <repo-url>
cd decodebot-ai
python main.py
```

No dependencies required — only Python 3.12+.

## Usage

```
$ python main.py

+==========================================+
|         D E C O D E B O T   A I         |
|   Rule-Based Conversational Agent        |
|              v1.0.0                      |
+==========================================+

Type 'help' to see what I can do.

You: hello
Bot: Hey there! What's on your mind?

You: help
Bot: [command list]

You: bye
Bot: Goodbye! Thanks for chatting!
```

## Architecture

DecodeBot uses a clean layered architecture:

- **Presentation Layer:** CLI REPL loop (`core/loop.py`)
- **Application Layer:** Intent dispatcher + response selector (`core/dispatcher.py`, `core/responder.py`)
- **Domain Layer:** Rule engine + session state (`core/rule_engine.py`, `core/session.py`)
- **Infrastructure Layer:** Config, logging, stats, history (`core/config.py`, `core/logger.py`, `core/stats.py`, `core/history.py`)

See `docs/ARCHITECTURE.md` and `SPEC-CHAT BOT.md` for full details.

## Testing

```bash
python -m pytest
```

The test suite includes:
- 8 mandatory compliance gate tests
- Unit, integration, regression, and edge-case tests
- Plugin interface and animation tests

## Documentation

- [Configuration](docs/CONFIGURATION.md)
- [Plugin Guide](docs/PLUGIN_GUIDE.md)
- [Hidden Commands](docs/HIDDEN_COMMANDS.md)
- [Full Specification](SPEC-CHAT BOT.md)

## License

MIT
