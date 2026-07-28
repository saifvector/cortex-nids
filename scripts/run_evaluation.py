#!/usr/bin/env python
"""
Model Evaluation pipeline runner for NIDS.
Loads optimized (and fallback original) models, evaluates them on the test partition,
generates all visualizations and reports, and ranks the models — without retraining.
"""
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.train import load_processed_data
from src.evaluator import ModelEvaluator, load_evaluation_models
from src.model_comparator import (
    rank_models,
    identify_leaders,
    build_strengths_weaknesses,
    generate_markdown_report,
    generate_html_report,
)


TARGET_MODELS = ["random_forest", "extra_trees", "xgboost", "lightgbm", "catboost"]


def main() -> None:
    # ── Initialise configuration and logging ──────────────────────────────
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.evaluation")

    logger.info("=" * 60)
    logger.info("NIDS Model Evaluation & Performance Analysis Pipeline")
    logger.info("=" * 60)

    # ── Resolve paths ─────────────────────────────────────────────────────
    processed_dir  = get_absolute_path(settings.paths.processed_data_dir)
    models_dir     = get_absolute_path(settings.paths.models_dir)
    optimized_dir  = models_dir / "optimized"
    eval_dir       = get_absolute_path("reports/evaluation")
    ensure_directory(eval_dir)

    # ── Load processed splits ─────────────────────────────────────────────
    logger.info("Loading processed data splits from: %s", processed_dir)
    try:
        X_train, X_test, y_train, y_test = load_processed_data(processed_dir)
    except Exception as e:
        logger.critical("Failed to load processed splits: %s", e, exc_info=True)
        sys.exit(1)

    # ── Load models ───────────────────────────────────────────────────────
    models = load_evaluation_models(
        optimized_dir=optimized_dir,
        fallback_dir=models_dir,
        target_names=TARGET_MODELS,
    )
    if not models:
        logger.critical(
            "No model checkpoints could be loaded from %s or %s. "
            "Please run scripts/run_training.py and scripts/run_hyperparameter_tuning.py first.",
            optimized_dir, models_dir
        )
        sys.exit(1)

    # ── Evaluate ──────────────────────────────────────────────────────────
    evaluator = ModelEvaluator(
        output_dir=eval_dir,
        X_test=X_test,
        y_test=y_test,
        X_train=X_train,
        y_train=y_train,
    )

    metrics_df, class_reports = evaluator.evaluate_all(models)

    if metrics_df.empty:
        logger.critical("Evaluation produced no results. Exiting.")
        sys.exit(1)

    # ── Rank & compare ────────────────────────────────────────────────────
    ranked_df = rank_models(metrics_df)
    leaders   = identify_leaders(ranked_df)
    sw        = build_strengths_weaknesses(ranked_df, leaders)

    recommended = ranked_df.iloc[0]["Model"]
    logger.info("Recommended Model: %s", recommended)

    # ── Save CSV outputs ──────────────────────────────────────────────────
    eval_metrics_path   = eval_dir / "evaluation_metrics.csv"
    model_ranking_path  = eval_dir / "model_ranking.csv"
    class_report_path   = eval_dir / "classification_report.csv"

    metrics_df.to_csv(eval_metrics_path, index=False)
    logger.info("Evaluation metrics saved: %s", eval_metrics_path)

    ranked_df.to_csv(model_ranking_path, index=False)
    logger.info("Model ranking saved: %s", model_ranking_path)

    # Combine all per-model classification reports
    if class_reports:
        combined_cr = pd.concat(class_reports.values(), ignore_index=True)
        combined_cr.to_csv(class_report_path, index=False)
        logger.info("Classification report saved: %s", class_report_path)

    # ── Generate Markdown report ──────────────────────────────────────────
    md_report_path   = eval_dir / "evaluation_report.md"
    html_report_path = eval_dir / "evaluation_report.html"

    generate_markdown_report(
        ranked_df=ranked_df,
        leaders=leaders,
        class_reports=class_reports,
        strengths_weaknesses=sw,
        recommended_model=recommended,
        output_path=md_report_path,
        X_train_shape=X_train.shape,
        X_test_shape=X_test.shape,
    )

    generate_html_report(
        markdown_path=md_report_path,
        output_path=html_report_path,
    )

    # ── Final console summary ─────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Model Evaluation completed successfully.")
    logger.info("Recommended Model: %s", recommended)
    logger.info("=" * 60)
    logger.info("Category leaders:")
    for label, model in leaders.items():
        logger.info("  %-30s -> %s", label, model)
    logger.info("=" * 60)
    logger.info("Outputs saved to: %s", eval_dir)
    logger.info("  - evaluation_metrics.csv")
    logger.info("  - model_ranking.csv")
    logger.info("  - classification_report.csv")
    logger.info("  - evaluation_report.md")
    logger.info("  - evaluation_report.html")
    logger.info("  - plots/ (confusion matrices, ROC, PR, feature importance, ...)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
