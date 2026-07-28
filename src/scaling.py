"""
Scaling module for NIDS.
Supports StandardScaler, MinMaxScaler, and RobustScaler options.
"""
import logging
from typing import Union
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

from src.exceptions.custom_exceptions import DataPreprocessingError


class FeatureScaler:
    """
    OOP Feature Scaler supporting multiple scikit-learn scaling techniques.
    """

    def __init__(self, method: str = "standard"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.method = method.lower()
        self.scaler = self._init_scaler()

    def _init_scaler(self) -> Union[StandardScaler, MinMaxScaler, RobustScaler]:
        """Initializes the underlying scikit-learn scaler object."""
        if self.method == "standard":
            self.logger.info("Configuring StandardScaler.")
            return StandardScaler()
        elif self.method == "minmax":
            self.logger.info("Configuring MinMaxScaler.")
            return MinMaxScaler()
        elif self.method == "robust":
            self.logger.info("Configuring RobustScaler.")
            return RobustScaler()
        else:
            raise DataPreprocessingError(
                f"Unsupported scaling method: {self.method}. Choose 'standard', 'minmax', or 'robust'."
            )

    def fit(self, X: pd.DataFrame) -> "FeatureScaler":
        """Fits the scaler on the numeric columns of features DataFrame."""
        self.logger.info("Fitting scaler on training features...")
        try:
            # We assume features are numeric. Columns will be scaling targets.
            self.scaler.fit(X)
            return self
        except Exception as e:
            raise DataPreprocessingError(f"Failed to fit scaler: {e}") from e

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms features DataFrame using the fitted scaler."""
        self.logger.info("Transforming features using fitted scaler...")
        try:
            scaled_array = self.scaler.transform(X)
            # Reconstruct as a DataFrame to preserve feature headers
            scaled_df = pd.DataFrame(scaled_array, columns=X.columns, index=X.index)
            return scaled_df
        except Exception as e:
            raise DataPreprocessingError(f"Failed to scale features: {e}") from e

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fits and transforms features in one step."""
        return self.fit(X).transform(X)
