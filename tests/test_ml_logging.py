"""Phase 21 — ML logging tests (FR-227).

The ML Engine logs through the ``decodebot.ml`` logger hierarchy whose level
is independently configurable via ``ml_log_level`` while reusing the shared
RotatingFileHandler configured by ``decodebot.core.logger``.
"""

import logging
from logging.handlers import RotatingFileHandler

from decodebot.core.logger import setup_logging
from decodebot.ml import app_ml


class TestMlLoggerHierarchy:
    def test_ml_loggers_exist(self):
        assert logging.getLogger("decodebot.ml").name == "decodebot.ml"
        for name in ("decodebot.ml.trainer", "decodebot.ml.app_ml", "decodebot.ml.predictor"):
            logger = logging.getLogger(name)
            assert logger.name == name

    def test_ml_logger_is_subhierarchy(self):
        assert logging.getLogger("decodebot.ml.trainer").parent is logging.getLogger("decodebot.ml")


class TestMlLogLevelConfig:
    def test_ml_log_level_warning(self, tmp_path):
        logger = setup_logging({"log_dir": str(tmp_path), "ml_log_level": "WARNING"})
        try:
            ml_logger = logging.getLogger("decodebot.ml")
            assert ml_logger.level == logging.WARNING
        finally:
            logger.handlers.clear()

    def test_ml_log_level_debug(self, tmp_path):
        logger = setup_logging({"log_dir": str(tmp_path), "ml_log_level": "DEBUG"})
        try:
            ml_logger = logging.getLogger("decodebot.ml")
            assert ml_logger.level == logging.DEBUG
        finally:
            logger.handlers.clear()

    def test_ml_log_level_defaults_to_log_level(self, tmp_path):
        logger = setup_logging({"log_dir": str(tmp_path), "log_level": "ERROR"})
        try:
            assert logging.getLogger("decodebot.ml").level == logging.ERROR
        finally:
            logger.handlers.clear()

    def test_ml_logger_propagates_to_shared_handler(self, tmp_path):
        logger = setup_logging({"log_dir": str(tmp_path)})
        try:
            root_logger = logging.getLogger()
            assert any(
                isinstance(h, RotatingFileHandler) for h in root_logger.handlers
            ), "shared RotatingFileHandler missing (FR-096 reuse)"
            assert logging.getLogger("decodebot.ml").propagate is True
        finally:
            logger.handlers.clear()


class TestMlHandlerLogging:
    def test_pipeline_logs_under_ml_namespace(self, tmp_path, caplog):
        from decodebot.core.session import SessionState

        session = SessionState()
        session.config = {
            "ml_dataset": "iris",
            "ml_target_column": None,
            "ml_test_size": 0.2,
            "ml_random_state": 42,
            "knn_k": 5,
            "classifier_type": "knn",
            "scaler_type": "standard",
            "ml_missing_value_strategy": "error",
            "models_dir": str(tmp_path),
            "ml_outputs_dir": str(tmp_path),
            "ml_log_level": "INFO",
        }
        with caplog.at_level(logging.INFO, logger="decodebot.ml"):
            app_ml.handle_train(session)
        assert any(
            record.name.startswith("decodebot.ml") for record in caplog.records
        ), "ML pipeline produced no logs under decodebot.ml"

    def test_handlers_log_before_recovering(self, tmp_path, caplog):
        from decodebot.core.session import SessionState

        session = SessionState()
        session.config = {
            "ml_dataset": "missing_file.csv",
            "ml_target_column": "class",
            "models_dir": str(tmp_path),
            "ml_outputs_dir": str(tmp_path),
        }
        with caplog.at_level(logging.ERROR, logger="decodebot.ml"):
            result = app_ml.handle_train(session)
        assert result.startswith("ML error:")
        assert any(
            record.name == "decodebot.ml.app_ml" and record.levelno >= logging.ERROR
            for record in caplog.records
        ), "handler failed to log before recovering (FR-228)"
