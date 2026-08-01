import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(config: dict | None = None) -> logging.Logger:
    if config is None:
        config = {}
    log_dir = config.get("log_dir", "logs")
    log_level_str = config.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "decodebot.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    file_handler = RotatingFileHandler(
        log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    ml_level_str = config.get("ml_log_level", log_level_str).upper()
    ml_log_level_value = getattr(logging, ml_level_str, logging.INFO)
    ml_logger = logging.getLogger("decodebot.ml")
    ml_logger.setLevel(ml_log_level_value)
    ml_logger.propagate = True

    logger = logging.getLogger("decodebot")
    logger.info("Session started.")
    return logger
