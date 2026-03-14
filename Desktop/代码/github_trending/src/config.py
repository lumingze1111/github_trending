"""Configuration management for the GitHub Trending scraper."""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from src.exceptions import ConfigException


class Config:
    """Configuration loader with environment variable substitution."""

    REQUIRED_FIELDS = [
        "oss.access_key_id",
        "oss.access_key_secret",
        "oss.bucket_name",
        "dingtalk.webhook_url",
    ]

    @staticmethod
    def load(config_path: str = "config.yaml") -> Dict[str, Any]:
        """
        Load configuration from YAML file with environment variable substitution.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Configuration dictionary

        Raises:
            ConfigException: If config file not found or required fields missing
        """
        # Check if config file exists
        if not Path(config_path).exists():
            raise ConfigException(f"Config file not found: {config_path}")

        # Load YAML
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigException(f"Failed to parse config file: {e}")

        # Substitute environment variables
        config = Config._substitute_env_vars(config)

        # Validate required fields
        Config._validate_required_fields(config)

        logger.info(f"Configuration loaded from {config_path}")
        return config

    @staticmethod
    def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively substitute ${VAR_NAME} with environment variables.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with substituted values

        Raises:
            ConfigException: If required environment variable not set
        """
        if isinstance(config, dict):
            return {
                key: Config._substitute_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [Config._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME} pattern
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, config)

            for var_name in matches:
                env_value = os.getenv(var_name)
                if env_value is None:
                    raise ConfigException(
                        f"Environment variable ${{{var_name}}} not set"
                    )
                config = config.replace(f"${{{var_name}}}", env_value)

            return config
        else:
            return config

    @staticmethod
    def _validate_required_fields(config: Dict[str, Any]) -> None:
        """
        Validate that all required configuration fields are present.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigException: If required field is missing
        """
        for field_path in Config.REQUIRED_FIELDS:
            keys = field_path.split('.')
            value = config

            try:
                for key in keys:
                    value = value[key]

                if not value:
                    raise ConfigException(
                        f"Missing required config field: {field_path}"
                    )
            except (KeyError, TypeError):
                raise ConfigException(
                    f"Missing required config field: {field_path}"
                )
