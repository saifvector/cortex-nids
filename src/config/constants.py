"""
Constants configuration file.
Defines system-wide immutable constants used across NIDS modules.
"""
import os
import sys
from pathlib import Path

# Project paths — PyInstaller-aware resolution
# When frozen (running as .exe), bundled data files live under sys._MEIPASS.
# When running from source, resolve relative to this file's location.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default settings files
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "default_config.yaml"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"

# Environment types
ENV_DEV = "development"
ENV_STAGE = "staging"
ENV_PROD = "production"
VALID_ENVIRONMENTS = {ENV_DEV, ENV_STAGE, ENV_PROD}

# Log definitions
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

# Data schemas
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_RAW_DIR = DEFAULT_DATA_DIR / "raw"
DEFAULT_PROCESSED_DIR = DEFAULT_DATA_DIR / "processed"

# Model paths
DEFAULT_MODELS_DIR = PROJECT_ROOT / "models"

# Standard random state
GLOBAL_RANDOM_STATE = 42
