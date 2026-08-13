import sys

from decodebot.core.loop import run_session
from decodebot.core.config import load_config
from decodebot.core.logger import setup_logging


def run(config_overrides: dict | None = None) -> None:
    config = load_config()
    if config_overrides:
        config.update(config_overrides)
    logger = setup_logging(config)
    logger.info(
        "Application started with config: %s",
        {k: v for k, v in config.items() if k != "log_dir"},
    )
    try:
        run_session(config=config)
    except Exception:
        logger.exception("Fatal unhandled exception")
        sys.exit(1)
