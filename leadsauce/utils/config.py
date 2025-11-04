"""
Configuration management utilities
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from leadsauce.utils.constants import (
    APP_DIR,
    CONFIG_FILE,
    DEFAULT_CONFIG,
    LOG_DIR,
    PLUGINS_DIR,
    WORKFLOWS_DIR
)


class Config:
    """Configuration manager"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load_config()

    def _ensure_app_dir(self):
        """Ensure application directory exists"""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        self._ensure_app_dir()

        if not self.config_path.exists():
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(DEFAULT_CONFIG, config or {})
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        """Save configuration to file"""
        self._ensure_app_dir()
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise Exception(f"Could not save config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('output.format')
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation
        Example: config.set('output.format', 'json')
        """
        keys = key.split('.')
        config = self.config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config

    def reset(self):
        """Reset configuration to defaults"""
        self.config = DEFAULT_CONFIG.copy()
        self.save()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration"""
    return Config(config_path)


def init_config() -> Config:
    """Initialize configuration with defaults"""
    config = Config()
    config.save()
    return config


# Environment variable overrides
def get_env_config() -> Dict[str, Any]:
    """Get configuration overrides from environment variables"""
    env_config = {}

    # Map environment variables to config keys
    env_mappings = {
        'LEADSAUCE_API_ENDPOINT': 'api.endpoint',
        'LEADSAUCE_API_KEY': 'api.key',
        'LEADSAUCE_DB_URL': 'database.url',
        'LEADSAUCE_OUTPUT_FORMAT': 'output.format',
        'LEADSAUCE_LOG_LEVEL': 'logging.level',
        'OPENAI_API_KEY': 'openai.api_key',
        'LEADSAUCE_EMAIL_PASSWORD': 'email.password',
    }

    for env_var, config_key in env_mappings.items():
        value = os.getenv(env_var)
        if value:
            keys = config_key.split('.')
            current = env_config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value

    return env_config


def apply_env_overrides(config: Config):
    """Apply environment variable overrides to config"""
    env_config = get_env_config()

    def merge_dict(base: Dict, override: Dict):
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                merge_dict(base[key], value)
            else:
                base[key] = value

    merge_dict(config.config, env_config)
