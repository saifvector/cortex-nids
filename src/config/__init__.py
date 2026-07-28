"""
Configuration package initialization.
Exposes settings, constants, and the global ConfigManager.
"""

from .constants import (
    PROJECT_ROOT,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_ENV_FILE,
    ENV_DEV,
    ENV_STAGE,
    ENV_PROD,
    VALID_ENVIRONMENTS,
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FORMAT,
    DEFAULT_DATA_DIR,
    DEFAULT_RAW_DIR,
    DEFAULT_PROCESSED_DIR,
    DEFAULT_MODELS_DIR,
    GLOBAL_RANDOM_STATE,
)
from .settings import Settings, load_settings
from .config import ConfigManager

__all__ = [
    "PROJECT_ROOT",
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_ENV_FILE",
    "ENV_DEV",
    "ENV_STAGE",
    "ENV_PROD",
    "VALID_ENVIRONMENTS",
    "DEFAULT_LOG_DIR",
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_DATA_DIR",
    "DEFAULT_RAW_DIR",
    "DEFAULT_PROCESSED_DIR",
    "DEFAULT_MODELS_DIR",
    "GLOBAL_RANDOM_STATE",
    "Settings",
    "load_settings",
    "ConfigManager",
]
