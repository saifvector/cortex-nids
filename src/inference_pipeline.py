"""
Inference Pipeline module for NIDS.
Handles automatic input validation, missing feature handling, feature alignment,
preprocessing transformation, and model prediction execution.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import DataPreprocessingError, ConfigurationError

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Validates input network data schemas, aligns features, executes preprocessing,
    and retrieves model predictions & probabilities.
    """

    def __init__(
        self,
        preprocessing_pipeline: Any,
        expected_features: List[str],
        model: Any
    ):
        self.pipeline = preprocessing_pipeline
        self.expected_features = expected_features
        self.model = model
        self.expected_count = len(expected_features)

    @classmethod
    def load_default(cls) -> "InferencePipeline":
        """Loads default ModelLoader artifacts to construct default InferencePipeline."""
        from src.model_loader import ModelLoader
        loader = ModelLoader()
        model, _ = loader.load_best_model()
        pipeline = loader.load_preprocessing_pipeline()
        features = loader.load_feature_names()
        return cls(preprocessing_pipeline=pipeline, expected_features=features, model=model)

    def validate_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates input DataFrame against expected feature count, names, and types.
        Fills missing features with 0.0 and drops extra features gracefully.

        Args:
            df: Input network traffic DataFrame.

        Returns:
            Validated & aligned DataFrame containing expected features in exact order.
        """
        if df.empty:
            raise DataPreprocessingError("Input dataset for inference is empty.")

        missing_feats = [f for f in self.expected_features if f not in df.columns]
        extra_feats = [c for c in df.columns if c not in self.expected_features and c != "label"]

        if missing_feats:
            logger.warning(
                "Input data is missing %d expected feature(s): %s. Filling missing values with 0.0.",
                len(missing_feats), missing_feats
            )
            for f in missing_feats:
                df[f] = 0.0

        if extra_feats:
            logger.debug(
                "Input data contains %d extra feature(s) not in schema: %s. Filtering out extra columns.",
                len(extra_feats), extra_feats
            )

        # Align columns to exact expected order
        aligned_df = df[self.expected_features].copy()

        # Coerce numeric types & check for infinite/NaN values
        for col in aligned_df.columns:
            aligned_df[col] = pd.to_numeric(aligned_df[col], errors="coerce").fillna(0.0)
            aligned_df[col] = aligned_df[col].replace([np.inf, -np.inf], 0.0)

        return aligned_df

    def transform_and_predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Validates input data, applies preprocessing transformation if necessary,
        and executes model inference.

        Args:
            df: Input raw or preprocessed network traffic DataFrame.

        Returns:
            Tuple of (predictions array, probabilities matrix or None).
        """
        validated_df = self.validate_input(df)

        # Check if pipeline requires transformation or features are already aligned
        try:
            if hasattr(self.pipeline, "transform"):
                logger.debug("Applying preprocessing pipeline transform...")
                X_proc = self.pipeline.transform(validated_df)
            elif hasattr(self.pipeline, "scaler") and hasattr(self.pipeline.scaler, "transform"):
                X_proc = self.pipeline.scaler.transform(validated_df)
            else:
                X_proc = validated_df
        except Exception as e:
            logger.warning("Pipeline transform failed (%s). Proceeding with validated numeric DataFrame.", e)
            X_proc = validated_df

        logger.debug("Executing model inference on %d records...", len(X_proc))
        preds = self.model.predict(X_proc)

        probs: Optional[np.ndarray] = None
        if hasattr(self.model, "predict_proba"):
            try:
                probs = self.model.predict_proba(X_proc)
            except Exception as e:
                logger.warning("predict_proba call failed: %s", e)

        return preds, probs
