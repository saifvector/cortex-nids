"""
Model Loader module for NIDS Inference Engine.
Loads model checkpoints, preprocessing pipelines, feature schemas, and metadata.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib

from src.exceptions.custom_exceptions import ModelTrainingError, ConfigurationError
from src.utils.utils import ensure_directory, get_absolute_path, load_json

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Handles loading and caching of model artifacts, preprocessing pipelines,
    feature schemas, and versioning metadata.
    """

    def __init__(
        self,
        models_dir: Union[str, Path] = "models",
        processed_dir: Union[str, Path] = "data/processed"
    ):
        self.models_dir = get_absolute_path(models_dir)
        self.processed_dir = get_absolute_path(processed_dir)
        self._model_cache: Dict[str, Any] = {}

    def load_best_model(self) -> Tuple[Any, str]:
        """
        Loads the best performing model (best_model.joblib or fallback from models/optimized/).
        """
        best_model_path = self.models_dir / "best_model.joblib"
        if best_model_path.exists():
            logger.info("Loading primary best model from: %s", best_model_path)
            model = joblib.load(best_model_path)
            model_name = getattr(model, "__class__", type(model)).__name__
            return model, model_name

        # Fallback to optimized models
        optimized_dir = self.models_dir / "optimized"
        if optimized_dir.exists():
            for opt_file in ["extra_trees.joblib", "random_forest.joblib", "catboost.joblib"]:
                p = optimized_dir / opt_file
                if p.exists():
                    logger.info("Loading optimized fallback model from: %s", p)
                    return joblib.load(p), p.stem

        raise ModelTrainingError(f"No valid model checkpoint found in {self.models_dir}")

    def load_specific_model(self, model_name: str) -> Any:
        """
        Loads a specific model by name from models/optimized/ or models/.
        """
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        paths_to_check = [
            self.models_dir / "optimized" / f"{model_name}.joblib",
            self.models_dir / f"{model_name}.joblib"
        ]
        for p in paths_to_check:
            if p.exists():
                logger.info("Loading model '%s' from: %s", model_name, p)
                model = joblib.load(p)
                self._model_cache[model_name] = model
                return model

        raise ConfigurationError(f"Model checkpoint for '{model_name}' not found.")

    def load_preprocessing_pipeline(self) -> Any:
        """
        Loads the pre-fitted preprocessing pipeline joblib artifact.
        """
        paths = [
            self.processed_dir / "preprocessing_pipeline.joblib",
            self.models_dir / "preprocessing_pipeline.joblib"
        ]
        for p in paths:
            if p.exists():
                logger.info("Loading preprocessing pipeline from: %s", p)
                return joblib.load(p)

        raise ConfigurationError(f"Preprocessing pipeline not found in {self.processed_dir} or {self.models_dir}")

    def load_feature_names(self) -> List[str]:
        """
        Loads expected feature column names list.
        """
        paths = [
            self.processed_dir / "feature_names.json",
            self.models_dir / "feature_names.json"
        ]
        for p in paths:
            if p.exists():
                logger.info("Loading feature names from: %s", p)
                return load_json(p)

        raise ConfigurationError("feature_names.json artifact not found.")

    def load_metadata(self) -> Dict[str, Any]:
        """
        Loads training metadata JSON.
        """
        metadata_path = self.models_dir / "metadata.json"
        if metadata_path.exists():
            return load_json(metadata_path)
        logger.warning("metadata.json not found at %s. Returning default schema.", metadata_path)
        return {
            "model_version": "1.0.0",
            "training_date": "N/A",
            "dataset_version": "CICIDS2017",
            "feature_count": 20,
            "model_type": "Ensemble Classifier"
        }
