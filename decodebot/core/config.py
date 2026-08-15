import json
import os

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
    "ml_dataset": "iris",
    "ml_target_column": None,
    "ml_test_size": 0.2,
    "ml_random_state": 42,
    "knn_k": 5,
    "classifier_type": "knn",
    "scaler_type": "standard",
    "ml_missing_value_strategy": "error",
    "models_dir": "models/",
    "ml_outputs_dir": "outputs/",
    "ml_log_level": "INFO",
    "recommender_corpus": "builtin",
    "recommender_top_n": 3,
    "recommender_min_skills": 3,
    "recommender_threshold": 0.0,
    "recommender_random_state": 42,
    "rec_image_path": "",
    "rec_psm": 6,
    "rec_confidence_threshold": 0.80,
    "rec_max_file_mb": 10,
    "rec_max_dimension": 4096,
    "rec_output_dir": "outputs/",
    "rec_overwrite": False,
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
    "ml_dataset": str,
    "ml_target_column": (str, type(None)),
    "ml_test_size": (int, float),
    "ml_random_state": int,
    "knn_k": int,
    "classifier_type": str,
    "scaler_type": str,
    "ml_missing_value_strategy": str,
    "models_dir": str,
    "ml_outputs_dir": str,
    "ml_log_level": str,
    "recommender_corpus": str,
    "recommender_top_n": int,
    "recommender_min_skills": int,
    "recommender_threshold": (int, float),
    "recommender_random_state": int,
    "rec_image_path": str,
    "rec_psm": int,
    "rec_confidence_threshold": (int, float),
    "rec_max_file_mb": (int, float),
    "rec_max_dimension": int,
    "rec_output_dir": str,
    "rec_overwrite": bool,
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
            except Exception:
                pass
    return config
