"""
Constants configuration file.
Defines system-wide immutable constants used across NIDS modules.
"""
import os
from pathlib import Path

# Project paths
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
