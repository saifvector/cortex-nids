"""
Exceptions module initialization.
Exposes custom NIDS exceptions for clean package imports.
"""

from .custom_exceptions import (
    NIDSException,
    ConfigurationError,
    DataPreprocessingError,
    FeatureEngineeringError,
    ModelError,
    ModelTrainingError,
    ModelEvaluationError,
    ModelPredictionError,
    PipelineError,
)

__all__ = [
    "NIDSException",
    "ConfigurationError",
    "DataPreprocessingError",
    "FeatureEngineeringError",
    "ModelError",
    "ModelTrainingError",
    "ModelEvaluationError",
    "ModelPredictionError",
    "PipelineError",
]
