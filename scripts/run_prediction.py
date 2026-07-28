#!/usr/bin/env python
"""
Prediction Engine runner script for NIDS.
Loads trained model, preprocessing pipeline, and metadata, runs inference on an input CSV,
generates prediction results, summary JSON, and Markdown/HTML reports.
"""
import sys
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.prediction_service import PredictionService


def main() -> None:
    parser = argparse.ArgumentParser(description="NIDS Production Model Inference Engine")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/X_test.csv",
        help="Path to input network traffic CSV file for inference (default: data/processed/X_test.csv)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model name to load (default: best_model)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="predictions",
        help="Directory to save prediction artifacts and reports (default: predictions)"
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=10000,
        help="Number of rows to sample from input CSV for prediction run (0 for full dataset)"
    )

    args = parser.parse_args()

    # 1. Initialize configuration and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.prediction")

    logger.info("=" * 60)
    logger.info("NIDS Production Model Inference Engine")
    logger.info("=" * 60)

    # 2. Resolve paths
    input_path = get_absolute_path(args.input)
    output_dir = get_absolute_path(args.output_dir)
    ensure_directory(output_dir)

    if not input_path.exists():
        logger.critical("Input file for inference not found: %s", input_path)
        sys.exit(1)

    logger.info("Input traffic data file: %s", input_path)

    # 3. Load sample or full dataset
    if args.sample_size > 0:
        logger.info("Sampling first %d records from %s for prediction...", args.sample_size, input_path.name)
        input_data = pd.read_csv(input_path, nrows=args.sample_size)
    else:
        input_data = input_path

    # 4. Initialize Prediction Service
    try:
        service = PredictionService(output_dir=output_dir, model_name=args.model)
    except Exception as e:
        logger.critical("Failed to initialize Prediction Service: %s", e, exc_info=True)
        sys.exit(1)

    # 5. Run inference pipeline
    predictions_df, summary = service.run_prediction_pipeline(input_data)

    # 6. Console summary printout
    logger.info("=" * 60)
    logger.info("Prediction Pipeline Execution Finished Successfully.")
    logger.info("Total Records Processed: %d", summary["inference_metrics"]["total_records_predicted"])
    logger.info("Average Risk Score: %.2f / 100", summary["inference_metrics"]["average_risk_score"])
    logger.info("Average Latency: %.3f ms/record", summary["inference_metrics"]["average_latency_ms"])
    logger.info("=" * 60)
    logger.info("Attack Breakdown:")
    for atk, cnt in summary["attack_breakdown"].items():
        logger.info("  - %-30s : %d", atk, cnt)
    logger.info("=" * 60)
    logger.info("Risk Level Distribution:")
    for rk, cnt in summary["risk_level_breakdown"].items():
        logger.info("  - %-15s : %d", rk, cnt)
    logger.info("=" * 60)
    logger.info("Artifacts generated in %s:", output_dir)
    logger.info("  - prediction_results.csv")
    logger.info("  - prediction_summary.json")
    logger.info("  - prediction_report.md")
    logger.info("  - prediction_report.html")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
