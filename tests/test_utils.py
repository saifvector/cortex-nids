"""
Unit tests for general utility modules.
"""
import pytest
from pathlib import Path
from src.utils.utils import (
    get_absolute_path,
    ensure_directory,
    save_json,
    load_json,
    save_yaml,
    load_yaml,
)
from src.exceptions.custom_exceptions import ConfigurationError


def test_path_resolution():
    """Verify that relative path is correctly converted to absolute relative to project root."""
    rel_path = "data/raw"
    abs_path = get_absolute_path(rel_path)
    assert abs_path.is_absolute()
    assert abs_path.name == "raw"


def test_directory_creation(tmp_path):
    """Verify directories are successfully created by ensure_directory."""
    test_dir = tmp_path / "nids_test_subdir"
    assert not test_dir.exists()
    
    created_dir = ensure_directory(test_dir)
    assert created_dir.exists()
    assert created_dir.is_dir()


def test_json_utilities(tmp_path):
    """Verify saving and loading JSON file operations."""
    test_file = tmp_path / "test_file.json"
    test_data = {"key": "value", "number": 42}
    
    save_json(test_data, test_file)
    assert test_file.exists()
    
    loaded_data = load_json(test_file)
    assert loaded_data == test_data


def test_yaml_utilities(tmp_path):
    """Verify saving and loading YAML file operations."""
    test_file = tmp_path / "test_file.yaml"
    test_data = {"key": "value", "list": [1, 2, 3]}
    
    save_yaml(test_data, test_file)
    assert test_file.exists()
    
    loaded_data = load_yaml(test_file)
    assert loaded_data == test_data


def test_invalid_load_raises():
    """Verify loading non-existent files raises a ConfigurationError."""
    non_existent = Path("does_not_exist_12345.json")
    with pytest.raises(ConfigurationError):
        load_json(non_existent)
        
    with pytest.raises(ConfigurationError):
        load_yaml(non_existent)
