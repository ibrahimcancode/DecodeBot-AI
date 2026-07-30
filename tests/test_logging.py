import pytest
import os
import tempfile
import logging


class TestLogging:
    def _cleanup_logger(self):
        root = logging.getLogger()
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()

    def test_logger_creates_log_file(self):
        from decodebot.core.logger import setup_logging
        with tempfile.TemporaryDirectory() as tmp:
            try:
                config = {"log_dir": tmp, "log_level": "DEBUG"}
                logger = setup_logging(config)
                logger.info("Test log entry")
                for handler in logger.root.handlers:
                    handler.flush()
                    handler.close()
                self._cleanup_logger()
                log_file = os.path.join(tmp, "decodebot.log")
                assert os.path.isfile(log_file)
            finally:
                self._cleanup_logger()

    def test_logger_startup_message(self):
        from decodebot.core.logger import setup_logging
        with tempfile.TemporaryDirectory() as tmp:
            try:
                config = {"log_dir": tmp, "log_level": "DEBUG"}
                logger = setup_logging(config)
                logger.info("Session started.")
                for handler in logger.root.handlers:
                    handler.flush()
                    handler.close()
                self._cleanup_logger()
                log_file = os.path.join(tmp, "decodebot.log")
                with open(log_file) as f:
                    content = f.read()
                assert "Session started" in content
            finally:
                self._cleanup_logger()

    def test_log_level_respected(self):
        from decodebot.core.logger import setup_logging
        with tempfile.TemporaryDirectory() as tmp:
            try:
                config = {"log_dir": tmp, "log_level": "WARNING"}
                logger = setup_logging(config)
                logger.info("Should not appear")
                logger.warning("Should appear")
                for handler in logger.root.handlers:
                    handler.flush()
                    handler.close()
                self._cleanup_logger()
                log_file = os.path.join(tmp, "decodebot.log")
                with open(log_file) as f:
                    content = f.read()
                assert "Should not appear" not in content
                assert "Should appear" in content
            finally:
                self._cleanup_logger()
