"""
Custom exceptions module for the Network Intrusion Detection System (NIDS).
Provides a hierarchical structure for application-specific error handling.
"""

class NIDSException(Exception):
    """Base exception class for all NIDS operations."""
    def __init__(self, message: str = "An error occurred within the NIDS system", *args):
        super().__init__(message, *args)
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class ConfigurationError(NIDSException):
    """Raised when there is an issue parsing, validating, or finding configuration parameters."""
    pass


class DataPreprocessingError(NIDSException):
    """Raised when loading, cleaning, transforming, or preprocessing data fails."""
    pass


class FeatureEngineeringError(NIDSException):
    """Raised when extraction or formatting of features fails."""
    pass


class ModelError(NIDSException):
    """Base model exception for training, testing, or serialized model operations."""
    pass


class ModelTrainingError(ModelError):
    """Raised when training the machine learning model fails."""
    pass


class ModelEvaluationError(ModelError):
    """Raised when calculating metrics or validating predictions fails."""
    pass


class ModelPredictionError(ModelError):
    """Raised when running inferences or scores on new inputs fails."""
    pass


class PipelineError(NIDSException):
    """Raised when pipeline execution (training or inference) fails to orchestrate."""
    pass
