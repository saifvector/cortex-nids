"""
Settings module containing Pydantic schemas for runtime configuration validation.
Supports environment overrides and provides configuration management.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from src.exceptions.custom_exceptions import ConfigurationError
from src.config.constants import DEFAULT_ENV_FILE, VALID_ENVIRONMENTS


class ProjectSettings(BaseModel):
    name: str = "Machine Learning-Based Network Intrusion Detection System"
    version: str = "1.0.0"
    random_state: int = 42
    debug: bool = True


class PathsSettings(BaseModel):
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    external_data_dir: str = "data/external"
    models_dir: str = "models"
    logs_dir: str = "logs"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    console_output: bool = True
    file_output: bool = True
    log_filename: str = "nids_execution.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


class DataPrepSettings(BaseModel):
    target_column: str = "label"
    test_size: float = 0.2
    val_size: float = 0.1
    stratify: bool = True
    scaling_method: str = "standard"
    imputation_strategy: str = "median"


class FeaturesSettings(BaseModel):
    columns_to_drop: List[str] = Field(default_factory=list)
    label_mapping: Dict[str, int] = Field(default_factory=dict)


class ModelSettings(BaseModel):
    selected_model: str = "random_forest"
    logistic_regression: Dict[str, Any] = Field(default_factory=dict)
    decision_tree: Dict[str, Any] = Field(default_factory=dict)
    random_forest: Dict[str, Any] = Field(default_factory=dict)
    extra_trees: Dict[str, Any] = Field(default_factory=dict)
    xgboost: Dict[str, Any] = Field(default_factory=dict)
    lightgbm: Dict[str, Any] = Field(default_factory=dict)
    catboost: Dict[str, Any] = Field(default_factory=dict)


class EvaluationSettings(BaseModel):
    metrics: List[str] = Field(default_factory=list)


class PreprocessingSettings(BaseModel):
    scaling_method: str = "standard"
    variance_threshold: float = 0.0001
    correlation_threshold: float = 0.90
    top_n_mi: int = 20
    top_n_rfe: int = 20
    balancing_method: str = "smote" # none, smote, rus, class_weights
    test_size: float = 0.2
    random_state: int = 42


class TuningSettings(BaseModel):
    method: str = "randomized"
    cv_folds: int = 5
    n_iter: int = 5
    optimization_sample_size: int = 50000


class Settings(BaseModel):
    app_env: str = Field(default="development", alias="APP_ENV")
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    data_preparation: DataPrepSettings = Field(default_factory=DataPrepSettings)
    features: FeaturesSettings = Field(default_factory=FeaturesSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    preprocessing: PreprocessingSettings = Field(default_factory=PreprocessingSettings)
    tuning: TuningSettings = Field(default_factory=TuningSettings)

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in VALID_ENVIRONMENTS:
            raise ValueError(f"Environment must be one of {VALID_ENVIRONMENTS}, got: {v}")
        return v_lower


def load_raw_yaml(config_path: Path) -> Dict[str, Any]:
    """Helper function to load YAML from a path."""
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found at {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse YAML configuration: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Unexpected error loading YAML configuration: {e}") from e


def load_settings(config_path: Path, env_file_path: Path = DEFAULT_ENV_FILE) -> Settings:
    """
    Bootstrap the settings:
    1. Loads environment variables from the env file.
    2. Reads the YAML config file.
    3. Overwrites config variables with environment variables if they match (hierarchical structure).
    4. Instantiates and validates Settings model.
    """
    # 1. Load .env file
    if env_file_path.exists():
        load_dotenv(dotenv_path=env_file_path, override=True)

    # 2. Read YAML configuration
    yaml_config = load_raw_yaml(config_path)

    # 3. Environment variable overrides (e.g. APP_ENV, LOG_LEVEL)
    # Map high level environment variables to the setting keys
    app_env = os.getenv("APP_ENV", yaml_config.get("app_env", "development"))
    
    # Example of overriding sub-dictionary settings via env vars
    log_level_env = os.getenv("LOG_LEVEL")
    if log_level_env:
        if "logging" not in yaml_config:
            yaml_config["logging"] = {}
        yaml_config["logging"]["level"] = log_level_env

    # Pass the structure to the Settings constructor
    try:
        settings_instance = Settings(
            APP_ENV=app_env,
            project=yaml_config.get("project", {}),
            paths=yaml_config.get("paths", {}),
            logging=yaml_config.get("logging", {}),
            data_preparation=yaml_config.get("data_preparation", {}),
            features=yaml_config.get("features", {}),
            model=yaml_config.get("model", {}),
            evaluation=yaml_config.get("evaluation", {}),
            preprocessing=yaml_config.get("preprocessing", {}),
        )
        return settings_instance
    except Exception as e:
        raise ConfigurationError(f"Failed to validate settings: {e}") from e
