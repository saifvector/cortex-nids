"""
Unit tests for settings validation and configuration management.
"""
import os
import pytest
from pathlib import Path
from src.config.config import ConfigManager
from src.config.settings import Settings, load_settings
from src.exceptions.custom_exceptions import ConfigurationError
from src.config.constants import DEFAULT_CONFIG_FILE


def test_config_singleton():
    """Verify that ConfigManager behaves as a Singleton."""
    cm1 = ConfigManager()
    cm2 = ConfigManager()
    assert cm1 is cm2


def test_default_config_loading():
    """Verify that settings can load from the default configuration yaml."""
    assert DEFAULT_CONFIG_FILE.exists(), f"Default configuration file not found at {DEFAULT_CONFIG_FILE}"
    
    settings = load_settings(DEFAULT_CONFIG_FILE)
    assert isinstance(settings, Settings)
    assert settings.project.name == "Machine Learning-Based Network Intrusion Detection System"
    assert settings.logging.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_invalid_env_validation(monkeypatch):
    """Verify that configuration raises ConfigurationError on invalid app environment names."""
    invalid_yaml = DEFAULT_CONFIG_FILE.parent / "invalid_test_config.yaml"
    
    # Save a temporary config with an invalid environment
    import yaml
    with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    # Mutate env
    data["app_env"] = "invalid_env_name"
    
    with open(invalid_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
        
    monkeypatch.delenv("APP_ENV", raising=False)
        
    try:
        with pytest.raises(ConfigurationError):
            load_settings(invalid_yaml, env_file_path=Path("non_existent_env"))
    finally:
        if invalid_yaml.exists():
            invalid_yaml.unlink()


def test_env_override(monkeypatch):
    """Verify environment variables successfully override configuration settings."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_ENV", "production")
    
    settings = load_settings(DEFAULT_CONFIG_FILE, env_file_path=Path("non_existent_env"))
    assert settings.logging.level == "DEBUG"
    assert settings.app_env == "production"
