#!/usr/bin/env python
"""
Explainable Machine Learning (XAI) pipeline runner for NIDS.
Loads optimized models and test data, computes SHAP values, feature importances,
permutation importances, and instance explanations, saving plots, CSVs, and reports.
"""
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.train import load_processed_data
from src.explainability import ExplainabilityManager, load_all_models

TARGET_MODELS = ["extra_trees", "random_forest", "lightgbm", "xgboost", "catboost"]


def main() -> None:
    # 1. Initialize configuration and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.explainability")

    logger.info("=" * 60)
    logger.info("NIDS Explainable Machine Learning (XAI) Pipeline")
    logger.info("=" * 60)

    # 2. Resolve directory paths
    processed_dir = get_absolute_path(settings.paths.processed_data_dir)
    models_dir = get_absolute_path(settings.paths.models_dir)
    optimized_dir = models_dir / "optimized"
    output_dir = get_absolute_path("reports/explainability")
    ensure_directory(output_dir)

    # 3. Load test data
    logger.info("Loading test dataset from %s...", processed_dir)
    try:
        _, X_test, _, y_test = load_processed_data(processed_dir)
    except Exception as e:
        logger.critical("Failed to load processed dataset splits: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Load models
    models = load_all_models(models_dir, optimized_dir, TARGET_MODELS)
    if not models:
        logger.critical("No target models found to explain.")
        sys.exit(1)

    best_model_path = models_dir / "best_model.joblib"
    best_model = None
    if best_model_path.exists():
        try:
            best_model = joblib.load(best_model_path)
            logger.info("Loaded best model from %s", best_model_path)
        except Exception as e:
            logger.warning("Could not load best model from %s: %s", best_model_path, e)

    best_model_name = "extra_trees"
    if "extra_trees" not in models and len(models) > 0:
        best_model_name = list(models.keys())[0]

    # 5. Run Explainability Manager
    manager = ExplainabilityManager(
        output_dir=output_dir,
        X_test=X_test,
        y_test=y_test,
        models=models,
        best_model=best_model,
        best_model_name=best_model_name
    )

    results = manager.run_full_xai_pipeline()

    logger.info("=" * 60)
    logger.info("XAI Pipeline Completed Successfully.")
    logger.info("Generated reports and plots in: %s", output_dir)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
