"""
Preprocessing Pipeline orchestrator module for NIDS.
Integrates encoding, scaling, feature selection, and class balancing into a single serializable object.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
import joblib

from src.exceptions.custom_exceptions import DataPreprocessingError, ConfigurationError
from src.encoding import CategoricalEncoder
from src.feature_selection import FeatureSelector
from src.scaling import FeatureScaler

# Try-imports for imbalanced-learn
IBLEARN_AVAILABLE = False
try:
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler
    IBLEARN_AVAILABLE = True
except BaseException as e:
    import traceback
    traceback.print_exc()


class PreprocessingPipeline:
    """
    Orchestration pipeline for NIDS data preparation.
    Fits feature selection, encoding, and scaling on train set, and transforms test set.
    Supports joblib serialization for production deployment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}

        # Extract sub-settings
        self.scaling_method = self.config.get("scaling_method", "standard")
        self.var_threshold = self.config.get("variance_threshold", 0.0001)
        self.corr_threshold = self.config.get("correlation_threshold", 0.90)
        self.top_n_mi = self.config.get("top_n_mi", 20)
        self.top_n_rfe = self.config.get("top_n_rfe", 20)
        self.balancing_method = self.config.get("balancing_method", "smote").lower()
        self.random_state = self.config.get("random_state", 42)

        # Components
        self.encoder = CategoricalEncoder()
        self.selector = FeatureSelector(
            variance_threshold=self.var_threshold,
            correlation_threshold=self.corr_threshold,
            top_n_mi=self.top_n_mi,
            top_n_rfe=self.top_n_rfe,
            random_state=self.random_state
        )
        self.scaler = FeatureScaler(method=self.scaling_method)

        # Meta properties
        self.original_features: List[str] = []
        self.final_features: List[str] = []
        self.label_mapping: Dict[str, int] = {}
        self.is_fitted = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "PreprocessingPipeline":
        """
        Fits all preprocessors on the training set.
        """
        self.logger.info("Fitting Preprocessing Pipeline on training set...")
        self.original_features = X_train.columns.tolist()

        try:
            # 1. Fit Categorical Encoding
            self.encoder.fit_features(X_train)
            X_encoded = self.encoder.transform_features(X_train)

            self.encoder.fit_target(y_train)
            y_encoded = self.encoder.transform_target(y_train)
            self.label_mapping = self.encoder.label_mapping

            # 2. Fit Feature Selector
            self.selector.fit(X_encoded, y_encoded)
            X_selected = self.selector.transform(X_encoded)
            self.final_features = self.selector.selected_features

            # 3. Fit Scaler
            self.scaler.fit(X_selected)

            self.is_fitted = True
            self.logger.info("Preprocessing Pipeline successfully fitted.")
            return self
        except Exception as e:
            raise DataPreprocessingError(f"Failed to fit preprocessing pipeline: {e}") from e

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms features DataFrame through the fitted pipeline.
        """
        if not self.is_fitted:
            raise DataPreprocessingError("Pipeline must be fitted before transformation.")

        self.logger.info("Transforming DataFrame using fitted Preprocessing Pipeline...")
        try:
            # 1. Encode categorical columns
            X_encoded = self.encoder.transform_features(X)

            # 2. Feature selection (subset features)
            X_selected = self.selector.transform(X_encoded)

            # 3. Scaling
            X_scaled = self.scaler.transform(X_selected)

            return X_scaled
        except Exception as e:
            raise DataPreprocessingError(f"Failed to transform DataFrame: {e}") from e

    def transform_target(self, y: pd.Series) -> pd.Series:
        """Transforms target labels using the fitted label encoder."""
        if not self.is_fitted:
            raise DataPreprocessingError("Pipeline must be fitted before target transformation.")
        return self.encoder.transform_target(y)

    def fit_transform(self, X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Fits the pipeline and transforms training data."""
        self.fit(X_train, y_train)
        X_trans = self.transform(X_train)
        y_trans = self.transform_target(y_train)
        return X_trans, y_trans

    def apply_resampling(self, X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
        """
        Handles class imbalance on training set using SMOTE or RUS.
        Evaluates and returns resampled dataset and balance metrics.
        """
        self.logger.info("Applying resampling: method=%s", self.balancing_method)
        stats = {
            "before_balancing": {str(k): int(v) for k, v in y_train.value_counts().items()},
            "method": self.balancing_method,
            "resampled": False
        }

        if self.balancing_method == "none":
            self.logger.info("No resampling requested.")
            return X_train, y_train, stats

        if not IBLEARN_AVAILABLE:
            self.logger.warning("imbalanced-learn library not available. Skipping resampling steps.")
            return X_train, y_train, stats

        try:
            # Check unique classes count
            num_classes = y_train.nunique()
            if num_classes <= 1:
                self.logger.warning("Target has only 1 class. Skipping imbalance correction.")
                return X_train, y_train, stats

            if self.balancing_method == "smote":
                self.logger.info("Initializing SMOTE...")
                # Verify min samples for minority class (SMOTE requires k_neighbors+1, default is 5 neighbors, so 6 samples)
                min_class_size = y_train.value_counts().min()
                k_neighbors = min(5, max(1, min_class_size - 1))
                if min_class_size < 2:
                    self.logger.warning("Minority class has only %d sample(s). Cannot run SMOTE. Falling back to RUS.", min_class_size)
                    resampler = RandomUnderSampler(random_state=self.random_state)
                else:
                    resampler = SMOTE(k_neighbors=k_neighbors, random_state=self.random_state)
            elif self.balancing_method == "rus":
                self.logger.info("Initializing RandomUnderSampler...")
                resampler = RandomUnderSampler(random_state=self.random_state)
            else:
                self.logger.warning("Unsupported balancing method: '%s'. Skipping balancing.", self.balancing_method)
                return X_train, y_train, stats

            X_res, y_res = resampler.fit_resample(X_train, y_train)
            
            # Record post-resampling counts
            stats["after_balancing"] = {str(k): int(v) for k, v in y_res.value_counts().items()}
            stats["resampled"] = True
            self.logger.info("Resampling completed. Cleaned shape: %s -> %s", X_train.shape, X_res.shape)
            return X_res, y_res, stats

        except Exception as e:
            self.logger.exception("Error occurred during dataset resampling: %s", e)
            return X_train, y_train, stats

    def calculate_class_weights(self, y_train: pd.Series) -> Dict[int, float]:
        """
        Computes balanced class weights for estimator algorithms.
        """
        self.logger.info("Calculating class weights...")
        try:
            classes = np.unique(y_train)
            total_samples = len(y_train)
            weights = {}
            for cls in classes:
                count = (y_train == cls).sum()
                weights[int(cls)] = float(total_samples / (len(classes) * count))
            self.logger.info("Computed class weights: %s", weights)
            return weights
        except Exception as e:
            self.logger.exception("Failed to calculate class weights: %s", e)
            return {}

    def save(self, dest_path: Union[str, Path]) -> None:
        """Serializes the entire fitted pipeline state using joblib."""
        out_path = Path(dest_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info("Serializing pipeline to: %s", out_path)
        try:
            # We pack all state parameters into joblib
            pipeline_state = {
                "config": self.config,
                "encoder": self.encoder,
                "selector": self.selector,
                "scaler": self.scaler,
                "original_features": self.original_features,
                "final_features": self.final_features,
                "label_mapping": self.label_mapping,
                "is_fitted": self.is_fitted
            }
            joblib.dump(pipeline_state, out_path)
            self.logger.info("Pipeline saved successfully.")
        except Exception as e:
            raise DataPreprocessingError(f"Failed to serialize pipeline: {e}") from e

    @classmethod
    def load(cls, src_path: Union[str, Path]) -> "PreprocessingPipeline":
        """Loads and reconstructs the pipeline state from joblib file."""
        in_path = Path(src_path)
        if not in_path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {in_path}")

        try:
            pipeline_state = joblib.load(in_path)
            
            # Construct a new instance
            instance = cls(config=pipeline_state["config"])
            instance.encoder = pipeline_state["encoder"]
            instance.selector = pipeline_state["selector"]
            instance.scaler = pipeline_state["scaler"]
            instance.original_features = pipeline_state["original_features"]
            instance.final_features = pipeline_state["final_features"]
            instance.label_mapping = pipeline_state["label_mapping"]
            instance.is_fitted = pipeline_state["is_fitted"]
            
            return instance
        except Exception as e:
            raise DataPreprocessingError(f"Failed to load pipeline state: {e}") from e
