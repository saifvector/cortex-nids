"""
Training Orchestrator module for NIDS.
Coordinates loading data partitions, invoking the factory and trainer,
extracting feature importances, ranking algorithms, and selecting the best model.
"""
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple, Union
import pandas as pd
import numpy as np
import joblib
import xgboost
import lightgbm
import catboost
import sklearn

from src.exceptions.custom_exceptions import ModelTrainingError, ConfigurationError
from src.utils.utils import get_absolute_path, ensure_directory
from src.model_factory import ModelFactory
from src.model_trainer import ModelTrainer
from src.model_registry import get_supported_models


def load_processed_data(processed_dir: Union[str, Path]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Loads transformed CSV splits from the processed directory."""
    logger = logging.getLogger("NIDS.train")
    p_dir = get_absolute_path(processed_dir)
    logger.info("Loading processed splits from: %s", p_dir)

    try:
        X_train = pd.read_csv(p_dir / "X_train.csv")
        X_test = pd.read_csv(p_dir / "X_test.csv")
        # Read targets as Series (using squeeze=True or simply selecting the column)
        y_train_df = pd.read_csv(p_dir / "y_train.csv")
        y_test_df = pd.read_csv(p_dir / "y_test.csv")
        
        y_train = y_train_df.iloc[:, 0]
        y_test = y_test_df.iloc[:, 0]

        logger.info("Splits loaded. X_train: %s, y_train: %s. X_test: %s, y_test: %s",
                    X_train.shape, y_train.shape, X_test.shape, y_test.shape)
        return X_train, X_test, y_train, y_test
    except Exception as e:
        raise ModelTrainingError(f"Failed to load processed split files from {p_dir}: {e}") from e


def compute_class_weights(y: pd.Series) -> Dict[int, float]:
    """Dynamically calculates balanced class weights from target label counts."""
    classes = np.unique(y)
    total = len(y)
    weights = {}
    for cls in classes:
        count = (y == cls).sum()
        weights[int(cls)] = float(total / (len(classes) * count))
    return weights


def train_and_evaluate_all(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    settings: Any
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Orchestrates the training of all 7 registry classifiers.
    Saves models to disk, computes evaluation metrics, and gathers tree feature importances.
    """
    logger = logging.getLogger("NIDS.train")
    models_dir = get_absolute_path(settings.paths.models_dir)
    ensure_directory(models_dir)

    factory = ModelFactory()
    trainer = ModelTrainer()

    # Calculate class weights for class weight support
    class_weights = compute_class_weights(y_train)
    logger.info("Computed balanced training class weights: %s", class_weights)

    comparison_records = []
    trained_models = {}
    feature_importances = {}

    supported_models = get_supported_models()
    logger.info("Preparing to train %d models: %s", len(supported_models), supported_models)

    random_state = settings.project.random_state

    for model_name in supported_models:
        logger.info("--------------------------------------------------")
        logger.info("Training Model: %s", model_name)
        logger.info("--------------------------------------------------")

        # Fetch settings from configuration if present, else empty dict
        model_params = {}
        if hasattr(settings.model, model_name):
            model_params = getattr(settings.model, model_name)
            if hasattr(model_params, "model_dump"):
                model_params = model_params.model_dump()
            elif hasattr(model_params, "dict"):
                model_params = model_params.dict()

        try:
            # Instantiate model
            model_instance = factory.create_model(
                model_name=model_name,
                hyperparameters=model_params,
                random_state=random_state,
                class_weights=class_weights
            )

            # Fit and evaluate
            fitted_model, stats = trainer.train_and_profile(
                model_name=model_name,
                model_instance=model_instance,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                class_weights=class_weights
            )

            # Save model to disk
            model_file = models_dir / f"{model_name}.joblib"
            logger.info("Saving '%s' model to: %s", model_name, model_file)
            joblib.dump(fitted_model, model_file)

            # Keep reference
            trained_models[model_name] = fitted_model

            # Gather metrics
            record = {"Model": model_name}
            record.update(stats)
            comparison_records.append(record)

            # Feature importances extraction for tree models
            importances = None
            if hasattr(fitted_model, "feature_importances_"):
                importances = fitted_model.feature_importances_
            elif hasattr(fitted_model, "get_feature_importance"):
                # CatBoost uses get_feature_importance()
                importances = fitted_model.get_feature_importance()

            if importances is not None:
                feature_importances[model_name] = np.array(importances)
                logger.info("Extracted feature importances for tree-based model '%s'.", model_name)

        except Exception as e:
            logger.exception("Failed to train model '%s': %s", model_name, e)

    comparison_df = pd.DataFrame(comparison_records)
    return comparison_df, trained_models, feature_importances


def select_best_model(comparison_df: pd.DataFrame, trained_models: Dict[str, Any], settings: Any) -> Tuple[str, Any]:
    """
    Selects the best classifier using the configured priority metrics:
    1. Highest F1 Score
    2. Highest Recall
    3. Lowest False Positive Rate
    """
    logger = logging.getLogger("NIDS.train")
    if comparison_df.empty:
        raise ModelTrainingError("No models were successfully trained. Cannot select best model.")

    logger.info("Ranking models to select best performing classifier...")

    # Sort descending by F1 Score, descending by Recall, then ascending by False Positive Rate
    ranked_df = comparison_df.sort_values(
        by=["F1 Score", "Recall", "False Positive Rate"],
        ascending=[False, False, True]
    )

    best_model_name = ranked_df.iloc[0]["Model"]
    best_model_f1 = ranked_df.iloc[0]["F1 Score"]
    best_model_recall = ranked_df.iloc[0]["Recall"]
    best_model_fpr = ranked_df.iloc[0]["False Positive Rate"]

    logger.info("Best model selected: '%s' (F1: %.4f, Recall: %.4f, FPR: %.4f)",
                best_model_name, best_model_f1, best_model_recall, best_model_fpr)

    best_model_instance = trained_models[best_model_name]

    # Save to best_model.joblib
    models_dir = get_absolute_path(settings.paths.models_dir)
    best_model_path = models_dir / "best_model.joblib"
    logger.info("Saving best model joblib state to: %s", best_model_path)
    joblib.dump(best_model_instance, best_model_path)

    return best_model_name, best_model_instance


def compile_metadata(
    best_model_name: str,
    dataset_shape: tuple,
    feature_count: int,
    total_train_duration: float
) -> Dict[str, Any]:
    """Compiles training run metadata and package dependency versions."""
    metadata = {
        "model_name": best_model_name,
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_shape": {
            "rows": dataset_shape[0],
            "cols": dataset_shape[1]
        },
        "feature_count": feature_count,
        "training_duration_seconds": total_train_duration,
        "system_info": {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version()
        },
        "dependency_versions": {
            "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "lightgbm": lightgbm.__version__,
            "catboost": catboost.__version__
        }
    }
    return metadata
