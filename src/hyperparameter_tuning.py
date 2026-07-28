"""
Hyperparameter Tuning Orchestrator for NIDS.
Loads original models, runs model optimizer searches on stratified samples,
refits optimized configurations on full training sets, and profiles improvement deltas.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Tuple, Union
import pandas as pd
import numpy as np
import joblib

from src.exceptions.custom_exceptions import ModelTrainingError
from src.utils.utils import get_absolute_path, ensure_directory
from src.model_optimizer import ModelOptimizer
from src.model_trainer import ModelTrainer
from src.train import compute_class_weights


def load_trained_models(models_dir: Union[str, Path]) -> Dict[str, Any]:
    """Loads all previously trained classification models from the models folder."""
    logger = logging.getLogger("NIDS.hyperparameter_tuning")
    m_dir = get_absolute_path(models_dir)
    logger.info("Loading pre-trained checkpoints from: %s", m_dir)
    
    # 5 models targeted for optimization
    target_names = ["random_forest", "extra_trees", "xgboost", "lightgbm", "catboost"]
    original_models = {}
    
    for name in target_names:
        model_file = m_dir / f"{name}.joblib"
        if model_file.exists():
            try:
                original_models[name] = joblib.load(model_file)
                logger.debug("Successfully loaded pre-trained model checkpoint: '%s'", name)
            except Exception as e:
                logger.error("Failed to load model file '%s': %s", model_file, e)
        else:
            logger.warning("Pre-trained model checkpoint not found for: '%s'", name)
            
    return original_models


def tune_and_profile_all(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    original_models: Dict[str, Any],
    settings: Any
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Tuning Orchestration pipeline.
    Finds best parameters on sample data, refits on full dataset, and compares metrics.
    """
    logger = logging.getLogger("NIDS.hyperparameter_tuning")
    optimized_dir = get_absolute_path(settings.paths.models_dir) / "optimized"
    ensure_directory(optimized_dir)

    optimizer = ModelOptimizer()
    trainer = ModelTrainer()

    # Extract sample details from config
    sample_size = settings.tuning.optimization_sample_size
    search_method = settings.tuning.method
    cv_folds = settings.tuning.cv_folds
    n_iter = settings.tuning.n_iter
    random_state = settings.project.random_state

    # Subsample training splits for search phase
    X_train_sample, y_train_sample = optimizer.stratified_sample(
        X_train, y_train,
        sample_size=sample_size,
        random_state=random_state
    )

    # Class weights for fitting
    class_weights = compute_class_weights(y_train)

    comparison_records = []
    optimized_models = {}
    best_parameters = {}

    # Load original model training durations from Module 4 results CSV
    comparison_csv = get_absolute_path("reports/model_training/model_comparison.csv")
    original_durations = {}
    if comparison_csv.exists():
        try:
            comp_df = pd.read_csv(comparison_csv)
            for _, row in comp_df.iterrows():
                original_durations[row["Model"].lower().strip()] = float(row["Training Time"])
            logger.debug("Successfully loaded original training times: %s", original_durations)
        except Exception as e:
            logger.warning("Could not parse original training durations from CSV: %s", e)

    target_models = ["random_forest", "extra_trees", "xgboost", "lightgbm", "catboost"]
    for name in target_models:
        if name not in original_models:
            logger.warning("Skipping optimization for '%s' because original checkpoint is missing.", name)
            continue

        logger.info("==================================================")
        logger.info("Optimizing Classifier: %s", name)
        logger.info("==================================================")

        orig_model = original_models[name]

        # 1. Profile Original Model performance on test set (bypassing fit step)
        logger.info("Profiling original '%s' model metrics on test split...", name)
        try:
            _, orig_stats = trainer.train_and_profile(
                model_name=f"{name}_original",
                model_instance=orig_model,
                X_train=X_train.iloc[:10],  # Dummy splits, won't be fitted
                y_train=y_train.iloc[:10],
                X_test=X_test,
                y_test=y_test,
                fit_model=False
            )
            # Retrieve training time from stored durations
            orig_stats["Training Time"] = original_durations.get(name, 0.0)
        except Exception as e:
            logger.error("Failed to profile original model '%s': %s", name, e)
            continue

        # 2. Run Hyperparameter search CV on Stratified Sample
        try:
            # Create a fresh un-fitted instance of the model class
            from src.model_factory import ModelFactory
            factory = ModelFactory()
            # Fetch default model parameters
            model_params = {}
            if hasattr(settings.model, name):
                model_params = getattr(settings.model, name)
                if hasattr(model_params, "model_dump"):
                    model_params = model_params.model_dump()
                elif hasattr(model_params, "dict"):
                    model_params = model_params.dict()

            search_base_estimator = factory.create_model(
                model_name=name,
                hyperparameters=model_params,
                random_state=random_state,
                class_weights=class_weights
            )

            best_params, _ = optimizer.optimize_hyperparameters(
                model_name=name,
                estimator=search_base_estimator,
                X_train_sample=X_train_sample,
                y_train_sample=y_train_sample,
                search_method=search_method,
                cv_folds=cv_folds,
                n_iter=n_iter,
                random_state=random_state
            )
            best_parameters[name] = best_params

        except Exception as e:
            logger.exception("Failed during search optimization phase for '%s': %s", name, e)
            continue

        # 3. Refit optimized model parameters on FULL training set
        logger.info("Refitting optimized '%s' on FULL training dataset splits...", name)
        try:
            # Merge original params and best params
            final_hyperparameters = model_params.copy()
            final_hyperparameters.update(best_params)

            # Instantiate final optimized model
            optimized_estimator = factory.create_model(
                model_name=name,
                hyperparameters=final_hyperparameters,
                random_state=random_state,
                class_weights=class_weights
            )

            # Fit and profile full training time and test performance metrics
            fitted_optimized, opt_stats = trainer.train_and_profile(
                model_name=f"{name}_optimized",
                model_instance=optimized_estimator,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                class_weights=class_weights
            )

            # Save optimized model to models/optimized/ folder
            opt_file = optimized_dir / f"{name}.joblib"
            logger.info("Saving optimized '%s' model to: %s", name, opt_file)
            joblib.dump(fitted_optimized, opt_file)

            # Keep reference
            optimized_models[name] = fitted_optimized

        except Exception as e:
            logger.exception("Failed during full refitting/evaluation phase for '%s': %s", name, e)
            continue

        # 4. Compile comparison records
        # Store deltas
        comparison_records.append({
            "Model": name,
            # Original Metrics
            "Original F1": orig_stats["F1 Score"],
            "Original Recall": orig_stats["Recall"],
            "Original FPR": orig_stats["False Positive Rate"],
            "Original Accuracy": orig_stats["Accuracy"],
            "Original Precision": orig_stats["Precision"],
            "Original ROC AUC": orig_stats["ROC AUC"],
            # Optimized Metrics
            "Optimized F1": opt_stats["F1 Score"],
            "Optimized Recall": opt_stats["Recall"],
            "Optimized FPR": opt_stats["False Positive Rate"],
            "Optimized Accuracy": opt_stats["Accuracy"],
            "Optimized Precision": opt_stats["Precision"],
            "Optimized ROC AUC": opt_stats["ROC AUC"],
            # Training Times
            "Original Train Time (s)": orig_stats["Training Time"],
            "Optimized Train Time (s)": opt_stats["Training Time"],
            # Deltas
            "F1 Improvement": opt_stats["F1 Score"] - orig_stats["F1 Score"],
            "Recall Improvement": opt_stats["Recall"] - orig_stats["Recall"],
            "FPR Decrease": orig_stats["False Positive Rate"] - opt_stats["False Positive Rate"]
        })

    comparison_df = pd.DataFrame(comparison_records)
    return comparison_df, optimized_models, best_parameters
