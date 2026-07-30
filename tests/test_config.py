import pytest
import json
import os
import tempfile

from decodebot.core.config import load_config, DEFAULT_CONFIG


class TestConfig:
    def test_default_config_returned_when_no_file(self):
        config = load_config()
        assert config["bot_name"] == "DecodeBot"
        assert config["enable_colors"] is True
        assert config["debug_mode"] is False

    def test_config_keys_present(self):
        config = load_config()
        for key in DEFAULT_CONFIG:
            assert key in config

    def test_bot_name_configurable(self):
        import decodebot.core.config as cfg
        old_paths = cfg.CONFIG_PATHS[:]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cfg_path = os.path.join(tmp, "config.json")
                with open(cfg_path, "w") as f:
                    json.dump({"bot_name": "Rex"}, f)
                cfg.CONFIG_PATHS = [cfg_path]
                config = cfg.load_config()
                assert config["bot_name"] == "Rex"
        finally:
            cfg.CONFIG_PATHS = old_paths


class TestConfigEdgeCases:
    def test_malformed_json_falls_back(self):
        import decodebot.core.config as cfg
        old_paths = cfg.CONFIG_PATHS[:]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cfg_path = os.path.join(tmp, "config.json")
                with open(cfg_path, "w") as f:
                    f.write("not valid json")
                cfg.CONFIG_PATHS = [cfg_path]
                config = cfg.load_config()
                assert config["bot_name"] == "DecodeBot"
        finally:
            cfg.CONFIG_PATHS = old_paths

    def test_partial_config_uses_defaults_for_missing_keys(self):
        import decodebot.core.config as cfg
        old_paths = cfg.CONFIG_PATHS[:]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cfg_path = os.path.join(tmp, "config.json")
                with open(cfg_path, "w") as f:
                    json.dump({"bot_name": "TestBot"}, f)
                cfg.CONFIG_PATHS = [cfg_path]
                config = cfg.load_config()
                assert config["bot_name"] == "TestBot"
                assert config["enable_colors"] is True
        finally:
            cfg.CONFIG_PATHS = old_paths
