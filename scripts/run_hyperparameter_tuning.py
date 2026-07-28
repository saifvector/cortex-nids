#!/usr/bin/env python
"""
Main pipeline execution script for NIDS Hyperparameter Optimization.
Loads preprocessed splits, runs CV parameter searches on training samples,
refits models on full partitions, exports results, and generates performance reports.
"""
import sys
import json
import logging
from pathlib import Path

# Add project root to system paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.train import load_processed_data
from src.hyperparameter_tuning import load_trained_models, tune_and_profile_all


def main():
    # 1. Initialize configuration and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.hyperparameter_tuning")

    logger.info("==================================================")
    logger.info("NIDS Hyperparameter Optimization Pipeline Run")
    logger.info("==================================================")

    # 2. Resolve Paths
    processed_dir = get_absolute_path(settings.paths.processed_data_dir)
    models_dir = get_absolute_path(settings.paths.models_dir)
    optimized_dir = models_dir / "optimized"
    reports_dir = get_absolute_path("reports")

    ensure_directory(processed_dir)
    ensure_directory(optimized_dir)
    ensure_directory(reports_dir)

    # 3. Load processed splits
    try:
        X_train, X_test, y_train, y_test = load_processed_data(processed_dir)
    except Exception as e:
        logger.critical("Failed to load processed splits: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Load pre-trained models
    original_models = load_trained_models(models_dir)
    if not original_models:
        logger.critical("No pre-trained model checkpoints found in %s. Please run scripts/run_training.py first.", models_dir)
        sys.exit(1)

    # 5. Execute Hyperparameter tuning
    try:
        comparison_df, optimized_models, best_parameters = tune_and_profile_all(
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            original_models=original_models,
            settings=settings
        )
    except Exception as e:
        logger.critical("Failed during hyperparameter tuning run: %s", e, exc_info=True)
        sys.exit(1)

    if comparison_df.empty:
        logger.critical("No models were successfully tuned. Exiting.")
        sys.exit(1)

    # 6. Save Best Parameters and CSV Results
    best_params_json_path = optimized_dir / "best_parameters.json"
    results_csv_path = optimized_dir / "optimization_results.csv"
    models_csv_path = optimized_dir / "optimized_models.csv"

    try:
        # Save JSON
        with open(best_params_json_path, "w", encoding="utf-8") as f:
            json.dump(best_parameters, f, indent=4)
        logger.info("Best parameters JSON saved to: %s", best_params_json_path)

        # Save CSV reports
        comparison_df.to_csv(results_csv_path, index=False)
        comparison_df.to_csv(models_csv_path, index=False)
        logger.info("Optimization results CSVs saved successfully to: %s", optimized_dir)
    except Exception as e:
        logger.error("Failed to save parameter configurations: %s", e)

    # 7. Generate Parameter Comparison Markdown block
    param_comparison_md = ""
    for name, opt_params in best_parameters.items():
        param_comparison_md += f"### {name.replace('_', ' ').title()} Parameter Details\n"
        param_comparison_md += "| Parameter Key Name | Original Config Value | Optimized Search Value |\n"
        param_comparison_md += "| :--- | :---: | :---: |\n"
        
        orig_model = original_models[name]
        orig_params = orig_model.get_params() if hasattr(orig_model, "get_params") else {}

        for param_key, opt_val in opt_params.items():
            # Get original parameter value
            orig_val = orig_params.get(param_key, "N/A")
            param_comparison_md += f"| **{param_key}** | `{orig_val}` | `{opt_val}` |\n"
        param_comparison_md += "\n"

    # 8. Generate Markdown Tuning Report
    report_file = reports_dir / "optimization_report.md"
    logger.info("Generating Hyperparameter Optimization Report: %s...", report_file)
    try:
        # Performance rows
        perf_rows = ""
        for idx, row in comparison_df.iterrows():
            perf_rows += (
                f"| **{row['Model']}** | {row['Original F1']:.5f} | {row['Optimized F1']:.5f} | "
                f"**{row['F1 Improvement']:+.5f}** | {row['Original Recall']:.5f} | {row['Optimized Recall']:.5f} | "
                f"{row['Original FPR']:.5f} | {row['Optimized FPR']:.5f} |\n"
            )

        # Time rows
        time_rows = ""
        for idx, row in comparison_df.iterrows():
            time_rows += (
                f"| **{row['Model']}** | `{row['Original Train Time (s)']:.2f} s` | "
                f"`{row['Optimized Train Time (s)']:.2f} s` | "
                f"`{row['Optimized Train Time (s)'] / max(0.1, row['Original Train Time (s)']):.1f}x` |\n"
            )

        md_content = f"""# NIDS Hyperparameter Optimization Report

Report compiled dynamically on parameter search cross-validation and benchmark improvement deltas.

---

## ⚙️ Search Configuration
- **Optimization Strategy**: `{settings.tuning.method.upper()} SEARCH`
- **Cross-Validation Scheme**: `StratifiedKFold ({settings.tuning.cv_folds}-Fold CV)`
- **Search Iteration Limit**: `{settings.tuning.n_iter} parameter sets`
- **Stratified Training Sample Size**: `{settings.tuning.optimization_sample_size:,} records` (used for parameter evaluation to prevent memory issues)
- **Refitting Dataset**: **FULL Training Partition** (`{X_train.shape[0]:,} records`)

---

## 📈 Performance Improvement Profile
Comparison of classification metrics on test partition.

| Model / Estimator | Original F1 | Optimized F1 | F1 Delta | Original Recall | Optimized Recall | Original FPR | Optimized FPR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{perf_rows}

---

## ⏱️ Training Duration & Compute Profiling
Comparison of fitting execution times on the full training dataset.

| Model / Estimator | Original Fit Time | Optimized Fit Time | Multiplier (Opt/Orig) |
| :--- | :---: | :---: | :---: |
{time_rows}

---

## 🛠️ Hyperparameter Value Comparison
Detailed view of changed hyperparameters after tuning.

{param_comparison_md}

---
*Report generated automatically by NIDS Hyperparameter Optimization pipeline runner.*
"""

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Hyperparameter Optimization Report successfully saved at: %s", report_file)

        # Log details to terminal
        for idx, row in comparison_df.iterrows():
            logger.info("Model '%s' Tuning Complete. F1 Delta: %+.5f. Optimized Train Time: %.2fs.",
                        row["Model"], row["F1 Improvement"], row["Optimized Train Time (s)"])

    except Exception as e:
        logger.exception("Failed to generate Hyperparameter Optimization Report: %s", e)

    logger.info("==================================================")
    logger.info("Hyperparameter Optimization completed successfully.")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
