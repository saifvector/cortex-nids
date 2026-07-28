"""
Utility functions module for NIDS.
Includes helpers for filesystem management, directory creation, and file validation.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Union

from src.config.constants import PROJECT_ROOT
from src.exceptions.custom_exceptions import NIDSException, ConfigurationError


def get_absolute_path(path: Union[str, Path]) -> Path:
    """
    Resolves a path against the project root if it is relative.
    Returns an absolute Path object.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensures a directory exists, creating it if necessary.
    """
    abs_path = get_absolute_path(path)
    try:
        abs_path.mkdir(parents=True, exist_ok=True)
        return abs_path
    except Exception as e:
        raise NIDSException(f"Failed to create directory at {abs_path}: {e}") from e


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file safely.
    """
    abs_path = get_absolute_path(path)
    if not abs_path.exists():
        raise ConfigurationError(f"YAML file not found at {abs_path}")
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise ConfigurationError(f"Failed to read/parse YAML at {abs_path}: {e}") from e


def save_yaml(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Save data to a YAML file safely.
    """
    abs_path = get_absolute_path(path)
    ensure_directory(abs_path.parent)
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except Exception as e:
        raise NIDSException(f"Failed to write YAML file at {abs_path}: {e}") from e


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file safely.
    """
    abs_path = get_absolute_path(path)
    if not abs_path.exists():
        raise ConfigurationError(f"JSON file not found at {abs_path}")
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to read/parse JSON at {abs_path}: {e}") from e


def save_json(data: Dict[str, Any], path: Union[str, Path], indent: int = 4) -> None:
    """
    Save data to a JSON file safely.
    """
    abs_path = get_absolute_path(path)
    ensure_directory(abs_path.parent)
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise NIDSException(f"Failed to write JSON file at {abs_path}: {e}") from e
