# Configuration Guide

DecodeBot AI supports an optional `config.json` file at the project root.

## Available Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `bot_name` | str | `"DecodeBot"` | Display name used in banner and prompts |
| `enable_colors` | bool | `true` | Toggle ANSI color output |
| `debug_mode` | bool | `false` | Enable verbose console diagnostics |
| `developer_mode` | bool | `false` | Unlock hidden developer commands |
| `log_level` | str | `"INFO"` | Minimum log level (DEBUG, INFO, WARNING, ERROR) |
| `log_dir` | str | `"logs"` | Directory for log files |
| `history_size` | int | `100` | Max conversation history entries |
| `enable_time_aware_greeting` | bool | `false` | Add time-of-day to greetings |
| `enable_emoji_greeting` | bool | `false` | Recognize emoji greetings |
| `plain_mode` | bool | `false` | Disable non-ASCII characters |

## Example

```json
{
    "bot_name": "MyBot",
    "enable_colors": true,
    "debug_mode": true
}
```

If `config.json` is absent or malformed, the application uses built-in defaults without crashing.
