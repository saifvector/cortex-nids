"""
Utilities package initialization.
Exposes logging setup and file IO utility helpers.
"""

from .logging import configure_logging, get_logger
from .utils import (
    get_absolute_path,
    ensure_directory,
    load_yaml,
    save_yaml,
    load_json,
    save_json,
)

try:
    from .visualization import Visualizer
except ImportError:
    Visualizer = None  # Lazy/Optional import for visualization

__all__ = [
    "configure_logging",
    "get_logger",
    "get_absolute_path",
    "ensure_directory",
    "load_yaml",
    "save_yaml",
    "load_json",
    "save_json",
    "Visualizer",
]
