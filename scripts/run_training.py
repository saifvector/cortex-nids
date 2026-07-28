#!/usr/bin/env python
"""
Main pipeline execution script for NIDS Classifier Model Training.
Loads preprocessed splits, fits 7 classifiers, ranks performance,
identifies best model, saves metadata and generates performance reports.
"""
import sys
import json
import logging
import time
from pathlib import Path

# Add project root to system paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.train import load_processed_data, train_and_evaluate_all, select_best_model, compile_metadata


def main():
    # 1. Initialize configuration and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.model_training")

    logger.info("==================================================")
    logger.info("NIDS Classifier Model Training Pipeline Run")
    logger.info("==================================================")

    # 2. Resolve Paths
    processed_dir = get_absolute_path(settings.paths.processed_data_dir)
    models_dir = get_absolute_path(settings.paths.models_dir)
    reports_dir = get_absolute_path("reports/model_training")

    ensure_directory(processed_dir)
    ensure_directory(models_dir)
    ensure_directory(reports_dir)

    # 3. Load processed splits
    try:
        X_train, X_test, y_train, y_test = load_processed_data(processed_dir)
    except Exception as e:
        logger.critical("Failed to load processed splits: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Fit and Evaluate all 7 Classifiers
    time_start = time.perf_counter()
    try:
        comparison_df, trained_models, feature_importances = train_and_evaluate_all(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            settings=settings
        )
    except Exception as e:
        logger.critical("Failed during training execution phase: %s", e, exc_info=True)
        sys.exit(1)
    
    total_train_duration = time.perf_counter() - time_start

    # 5. Select Best Classifier
    try:
        best_model_name, best_model_instance = select_best_model(
            comparison_df=comparison_df,
            trained_models=trained_models,
            settings=settings
        )
    except Exception as e:
        logger.critical("Failed during best model selection phase: %s", e, exc_info=True)
        sys.exit(1)

    # 6. Save Comparison Table
    comparison_csv_path = reports_dir / "model_comparison.csv"
    try:
        # Sort model rankings by the same criteria: F1 Score desc, Recall desc, FPR asc
        comparison_ranked = comparison_df.sort_values(
            by=["F1 Score", "Recall", "False Positive Rate"],
            ascending=[False, False, True]
        )
        comparison_ranked.to_csv(comparison_csv_path, index=False)
        logger.info("Comparison table saved to: %s", comparison_csv_path)
    except Exception as e:
        logger.error("Failed to save comparison CSV: %s", e)

    # 7. Compile Run Metadata
    metadata = compile_metadata(
        best_model_name=best_model_name,
        dataset_shape=X_train.shape,
        feature_count=X_train.shape[1],
        total_train_duration=total_train_duration
    )
    metadata_path = models_dir / "metadata.json"
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        logger.info("Run metadata JSON saved to: %s", metadata_path)
    except Exception as e:
        logger.error("Failed to write metadata JSON: %s", e)

    # 8. Generate Feature Importances Tables
    importance_md = ""
    for model_name, importances in feature_importances.items():
        importance_md += f"### {model_name.replace('_', ' ').title()} Feature Importance\n"
        importance_md += "| Rank | Feature Variable Name | Weight Score |\n"
        importance_md += "| :---: | :--- | :---: |\n"
        
        # Sort features by importance descending
        sorted_indices = np.argsort(importances)[::-1]
        for rank, idx in enumerate(sorted_indices[:10], start=1):
            feat_name = X_train.columns[idx]
            weight = importances[idx]
            importance_md += f"| {rank} | **{feat_name}** | `{weight:.6f}` |\n"
        importance_md += "\n"

    # 9. Generate Markdown Training Report
    report_file = reports_dir / "training_report.md"
    logger.info("Generating Model Training Report: %s...", report_file)
    try:
        # Construct markdown content
        ranking_rows = ""
        for idx, row in comparison_ranked.iterrows():
            ranking_rows += (
                f"| **{row['Model']}** | {row['F1 Score']:.5f} | {row['Recall']:.5f} | "
                f"{row['False Positive Rate']:.5f} | {row['Accuracy']:.5f} | {row['Precision']:.5f} |\n"
            )

        duration_rows = ""
        for idx, row in comparison_ranked.iterrows():
            duration_rows += (
                f"| **{row['Model']}** | `{row['Training Time']:.3f} s` | "
                f"`{row['Prediction Time']:.3f} s` | `{row['Memory Usage']:.2f} MB` |\n"
            )

        md_content = f"""# NIDS Machine Learning Model Training Report

Report compiled dynamically on model fitting telemetry and classification benchmarks.

---

## 🏆 Best Performing Model
- **Algorithm Selected**: `{best_model_name.upper().replace('_', ' ')}`
- **F1 Score (Macro)**: `{comparison_ranked.iloc[0]['F1 Score']:.5f}`
- **Recall (Macro)**: `{comparison_ranked.iloc[0]['Recall']:.5f}`
- **False Positive Rate**: `{comparison_ranked.iloc[0]['False Positive Rate']:.5f}`
- **Model Storage Reference**: `models/best_model.joblib`

---

## 📊 Model Ranking Summary
Ranked descending by **F1 Score**, then **Recall**, then ascending **False Positive Rate**.

| Algorithm / Classifier | F1 Score (Macro) | Recall (Macro) | False Positive Rate | Accuracy | Precision |
| :--- | :---: | :---: | :---: | :---: | :---: |
{ranking_rows}

---

## ⏱️ Training Duration & System Profiling
Summary of compute times and memory footprint differentials during training.

| Algorithm / Classifier | Training Duration | Prediction Latency | Memory Consumption |
| :--- | :---: | :---: | :---: |
{duration_rows}

- **Total Execution Time**: `{total_train_duration:.2f} seconds`

---

## 🌲 Tree-based Classifier Feature Importances
Top 10 relative feature variable importances mapped dynamically across fitted tree estimators.

{importance_md}

---

## ⚙️ Environment & Package Versions
- **Operating System**: `{metadata['system_info']['os']} ({metadata['system_info']['os_release']})`
- **Python Version**: `{metadata['system_info']['python_version']}`
- **Scikit-Learn Version**: `{metadata['dependency_versions']['scikit-learn']}`
- **XGBoost Version**: `{metadata['dependency_versions']['xgboost']}`
- **LightGBM Version**: `{metadata['dependency_versions']['lightgbm']}`
- **CatBoost Version**: `{metadata['dependency_versions']['catboost']}`

---
*Report generated automatically by NIDS Model Training pipeline runner.*
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Model Training Report successfully saved at: %s", report_file)

    except Exception as e:
        logger.exception("Failed to generate Model Training Report: %s", e)

    logger.info("==================================================")
    logger.info("Model Training Pipeline Completed Successfully.")
    logger.info("Best Model: %s", best_model_name)
    logger.info("==================================================")


if __name__ == "__main__":
    main()
