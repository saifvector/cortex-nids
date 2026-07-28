"""
Logging Configuration module.
Initializes the system logger with console and rotating file outputs.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config.settings import Settings
from src.config.constants import PROJECT_ROOT


def configure_logging(settings: Settings) -> None:
    """
    Configure the root logger with the specified settings.
    Creates the logs directory if file logging is enabled.
    """
    log_config = settings.logging
    paths_config = settings.paths

    # Resolve logs directory path
    log_dir = Path(paths_config.logs_dir)
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir

    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    
    # Check if handlers have already been configured (prevents double handlers)
    if root_logger.hasHandlers():
        return

    # Parse and set logging level
    level_name = log_config.level.upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter(log_config.format)

    # Console Handler
    if log_config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File Handler (Rotating)
    if log_config.file_output:
        log_file = log_dir / log_config.log_filename
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.max_bytes,
            backupCount=log_config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Helper function to get a named logger.
    """
    return logging.getLogger(name)
