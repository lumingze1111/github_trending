# tests/test_config.py
import pytest
import os
import tempfile
from pathlib import Path
from src.config import Config
from src.exceptions import ConfigException


def test_load_config_success(tmp_path):
    # Create temporary config file
    config_content = """
scraper:
  headless: true
  timeout: 30

database:
  path: "/tmp/test.db"

oss:
  access_key_id: ${OSS_ACCESS_KEY_ID}
  access_key_secret: ${OSS_ACCESS_KEY_SECRET}
  bucket_name: test-bucket
  endpoint: oss-cn-test.aliyuncs.com

dingtalk:
  webhook_url: ${DINGTALK_WEBHOOK_URL}
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)

    # Set environment variables
    os.environ["OSS_ACCESS_KEY_ID"] = "test_key"
    os.environ["OSS_ACCESS_KEY_SECRET"] = "test_secret"
    os.environ["DINGTALK_WEBHOOK_URL"] = "https://test.webhook.url"

    # Load config
    config = Config.load(str(config_file))

    assert config["scraper"]["headless"] is True
    assert config["scraper"]["timeout"] == 30
    assert config["oss"]["access_key_id"] == "test_key"
    assert config["oss"]["access_key_secret"] == "test_secret"
    assert config["oss"]["bucket_name"] == "test-bucket"
    assert config["dingtalk"]["webhook_url"] == "https://test.webhook.url"


def test_load_config_missing_file():
    with pytest.raises(ConfigException, match="Config file not found"):
        Config.load("/nonexistent/config.yaml")


def test_load_config_missing_required_env_var(tmp_path):
    config_content = """
oss:
  access_key_id: ${MISSING_VAR}
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)

    # Ensure env var doesn't exist
    os.environ.pop("MISSING_VAR", None)

    with pytest.raises(ConfigException, match="Environment variable.*not set"):
        Config.load(str(config_file))


def test_validate_required_fields_success():
    config = {
        "oss": {
            "access_key_id": "test",
            "access_key_secret": "test",
            "bucket_name": "test"
        },
        "dingtalk": {
            "webhook_url": "https://test.url"
        }
    }

    # Should not raise
    Config._validate_required_fields(config)


def test_validate_required_fields_missing():
    config = {
        "oss": {
            "access_key_id": "test"
            # Missing access_key_secret and bucket_name
        }
    }

    with pytest.raises(ConfigException, match="Missing required config"):
        Config._validate_required_fields(config)
