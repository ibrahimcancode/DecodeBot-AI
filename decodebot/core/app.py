import sys

from decodebot.core.loop import run_session
from decodebot.core.config import load_config
from decodebot.core.logger import setup_logging


def run() -> None:
    config = load_config()
    logger = setup_logging(config)
    logger.info("Application started with config: %s", {k: v for k, v in config.items() if k != "log_dir"})
    try:
        run_session()
    except Exception:
        logger.exception("Fatal unhandled exception")
        sys.exit(1)
