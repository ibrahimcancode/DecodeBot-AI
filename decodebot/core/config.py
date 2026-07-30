import json
import os
import logging

DEFAULT_CONFIG: dict = {
    "bot_name": "DecodeBot",
    "enable_colors": True,
    "debug_mode": False,
    "developer_mode": False,
    "log_level": "INFO",
    "log_dir": "logs",
    "history_size": 100,
    "enable_time_aware_greeting": False,
    "enable_emoji_greeting": False,
    "plain_mode": False,
    "enable_animations": True,
    "reduced_motion": False,
    "typewriter_speed": 0.015,
}

CONFIG_SCHEMA: dict = {
    "bot_name": str,
    "enable_colors": bool,
    "debug_mode": bool,
    "developer_mode": bool,
    "log_level": str,
    "log_dir": str,
    "history_size": int,
    "enable_time_aware_greeting": bool,
    "enable_emoji_greeting": bool,
    "plain_mode": bool,
    "enable_animations": bool,
    "reduced_motion": bool,
    "typewriter_speed": (int, float),
}

CONFIG_PATHS = [
    os.path.join(os.getcwd(), "config.json"),
]


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    for path in CONFIG_PATHS:
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    user_config = json.load(f)
                if not isinstance(user_config, dict):
                    raise ValueError("config root is not a JSON object")
                for key, value in user_config.items():
                    expected_type = CONFIG_SCHEMA.get(key)
                    if expected_type is None:
                        continue
                    if isinstance(value, expected_type):
                        config[key] = value
                    else:
                        pass
            except Exception as e:
                pass
    return config
