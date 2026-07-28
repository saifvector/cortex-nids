"""
Model Factory module for NIDS.
Instantiates classifier estimators, propagating random seeds, parallel jobs,
and class balancing weights based on model requirements.
"""
import logging
from typing import Any, Dict, Optional
from src.model_registry import MODEL_REGISTRY
from src.exceptions.custom_exceptions import ConfigurationError


class ModelFactory:
    """
    OOP Model Factory designed to instantiate classification estimators.
    Handles framework-specific differences for random states, thread safety, and weights.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_model(
        self,
        model_name: str,
        hyperparameters: Dict[str, Any],
        random_state: int,
        class_weights: Optional[Dict[int, float]] = None
    ) -> Any:
        """
        Instantiates the requested model class, configuring class weights, threads, and random states.
        """
        model_key = model_name.lower().strip()
        if model_key not in MODEL_REGISTRY:
            raise ConfigurationError(
                f"Model '{model_name}' is not supported in MODEL_REGISTRY. "
                f"Supported options: {list(MODEL_REGISTRY.keys())}"
            )

        model_class = MODEL_REGISTRY[model_key]
        params = hyperparameters.copy()

        self.logger.info("Instantiating classifier '%s' using factory...", model_key)

        # 1. Translate hyperparameters where names differ from scikit-learn constructors
        if model_key == "logistic_regression":
            if "c_value" in params:
                params["C"] = params.pop("c_value")

        # 2. Propagate random states (CatBoost uses random_seed, others use random_state)
        if model_key == "catboost":
            if "random_seed" not in params:
                params["random_seed"] = random_state
        else:
            if "random_state" not in params:
                params["random_state"] = random_state

        # 2. Configure Class Weights for handling imbalance
        if class_weights:
            # Scikit-learn and LightGBM accept class_weight in constructor
            if model_key in ["logistic_regression", "decision_tree", "random_forest", "extra_trees", "lightgbm"]:
                # Convert keys to integers if they are not already
                weights_dict = {int(k): float(v) for k, v in class_weights.items()}
                params["class_weight"] = weights_dict
                self.logger.debug("Applied class weight dictionary to '%s' constructor.", model_key)
            elif model_key == "catboost":
                # CatBoost accepts class_weights as list or dict
                weights_dict = {int(k): float(v) for k, v in class_weights.items()}
                params["class_weights"] = weights_dict
                self.logger.debug("Applied class_weights dictionary to CatBoost constructor.")
            elif model_key == "xgboost":
                # XGBoost doesn't accept class_weight in constructor for multiclass.
                # It will be handled in fitting via sample_weight inside ModelTrainer.
                self.logger.debug("XGBoost selected. Class weights will be mapped via sample_weight during fit().")

        # 3. Instantiate model
        try:
            model_instance = model_class(**params)
            return model_instance
        except Exception as e:
            raise ConfigurationError(f"Failed to instantiate model '{model_key}' with params {params}: {e}") from e
