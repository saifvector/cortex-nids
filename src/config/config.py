"""
Configuration Manager module.
Implements the Singleton pattern to provide a single, global access point
to validated application settings.
"""
import os
from pathlib import Path
from typing import Optional
from src.config.constants import DEFAULT_CONFIG_FILE, DEFAULT_ENV_FILE
from src.config.settings import Settings, load_settings


class ConfigManager:
    """
    Singleton Configuration Manager.
    Ensures settings are loaded, validated, and accessible across the system.
    """
    _instance: Optional["ConfigManager"] = None
    _settings: Optional[Settings] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def initialize(
        self, 
        config_path: Optional[Path] = None, 
        env_path: Optional[Path] = None
    ) -> None:
        """
        Loads and validates settings from the filesystem.
        Reads CONFIG_PATH environment variable if config_path is not specified.
        """
        # Resolve config path (parameter -> env variable -> default constant)
        if config_path is None:
            env_config_path = os.getenv("CONFIG_PATH")
            if env_config_path:
                config_path = Path(env_config_path)
            else:
                config_path = DEFAULT_CONFIG_FILE

        # Resolve env path (parameter -> default constant)
        if env_path is None:
            env_path = DEFAULT_ENV_FILE

        self._settings = load_settings(config_path, env_path)

    @property
    def settings(self) -> Settings:
        """
        Read-only property to retrieve loaded Settings.
        Auto-initializes if initialize() has not been called yet.
        """
        if self._settings is None:
            self.initialize()
        return self._settings
