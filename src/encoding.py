"""
Encoding module for NIDS.
Automatically detects object/categorical feature columns, applies One-Hot Encoding,
and applies Label Encoding to target category columns.
"""
import logging
from typing import Dict, List, Optional
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from src.exceptions.custom_exceptions import DataPreprocessingError


class CategoricalEncoder:
    """
    OOP Categorical Encoder class.
    Performs One-Hot Encoding on categorical features and Label Encoding on labels.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_ohe: Optional[OneHotEncoder] = None
        self.target_le: Optional[LabelEncoder] = None
        self.categorical_cols: List[str] = []
        self.label_mapping: Dict[str, int] = {}

    def fit_features(self, X: pd.DataFrame) -> "CategoricalEncoder":
        """
        Scans DataFrame and fits One-Hot Encoder on any object/categorical columns.
        """
        # Automatically detect categorical columns
        self.categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
        
        if self.categorical_cols:
            self.logger.info("Detected categorical columns in features: %s. Fitting One-Hot Encoder...", self.categorical_cols)
            try:
                # Use sparse_output=False for modern scikit-learn compatibility
                self.feature_ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
                self.feature_ohe.fit(X[self.categorical_cols])
            except Exception as e:
                raise DataPreprocessingError(f"Failed to fit One-Hot Encoder on features: {e}") from e
        else:
            self.logger.info("No categorical columns detected in features. Skipping One-Hot Encoder.")
            self.feature_ohe = None
            
        return self

    def transform_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms features DataFrame by One-Hot Encoding the detected categorical columns.
        """
        if not self.categorical_cols or self.feature_ohe is None:
            return X.copy()

        self.logger.info("Applying One-Hot Encoding on features...")
        try:
            X_encoded = X.copy()
            # Perform One-Hot encoding on categorical columns
            encoded_arr = self.feature_ohe.transform(X_encoded[self.categorical_cols])
            
            # Reconstruct column headers
            encoded_cols = self.feature_ohe.get_feature_names_out(self.categorical_cols)
            encoded_df = pd.DataFrame(encoded_arr, columns=encoded_cols, index=X_encoded.index)
            
            # Drop original categorical columns and concatenate encoded columns
            X_encoded = X_encoded.drop(columns=self.categorical_cols)
            X_encoded = pd.concat([X_encoded, encoded_df], axis=1)
            return X_encoded
        except Exception as e:
            raise DataPreprocessingError(f"Failed to transform categorical features: {e}") from e

    def fit_transform_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fits and transforms features in one step."""
        return self.fit_features(X).transform_features(X)

    def fit_target(self, y: pd.Series) -> "CategoricalEncoder":
        """Fits the LabelEncoder on target labels."""
        self.logger.info("Fitting LabelEncoder on target labels...")
        try:
            self.target_le = LabelEncoder()
            self.target_le.fit(y)
            # Expose class mappings
            self.label_mapping = {str(cls): int(idx) for idx, cls in enumerate(self.target_le.classes_)}
            self.logger.info("Resolved label mappings: %s", self.label_mapping)
            return self
        except Exception as e:
            raise DataPreprocessingError(f"Failed to fit LabelEncoder on labels: {e}") from e

    def transform_target(self, y: pd.Series) -> pd.Series:
        """Transforms target labels using the fitted LabelEncoder."""
        if self.target_le is None:
            raise DataPreprocessingError("LabelEncoder has not been fitted yet.")
        self.logger.info("Applying Label Encoding on target...")
        try:
            encoded_y = pd.Series(self.target_le.transform(y), index=y.index, name=y.name)
            return encoded_y
        except Exception as e:
            raise DataPreprocessingError(f"Failed to encode target: {e}") from e

    def fit_transform_target(self, y: pd.Series) -> pd.Series:
        """Fits and transforms target labels in one step."""
        return self.fit_target(y).transform_target(y)
