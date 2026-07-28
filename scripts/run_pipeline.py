#!/usr/bin/env python
"""
Execution entry point for the Network Intrusion Detection System.
Initializes configuration, configures logging, and runs the training or inference pipeline.
"""
import sys
import argparse
from pathlib import Path

# Add project root to path to run script directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory
from src.exceptions.custom_exceptions import NIDSException


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Machine Learning-Based Network Intrusion Detection System Runner"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to override default configuration file."
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Path to override default environment variables file."
    )
    parser.add_argument(
        "--mode",
        choices=["train", "predict"],
        default="train",
        help="Execution mode: train the model or predict with existing model."
    )
    return parser.parse_args()


def main():
    """Main orchestrator execution logic."""
    args = parse_args()

    # 1. Initialize Configuration Manager
    config_manager = ConfigManager()
    try:
        config_path = Path(args.config) if args.config else None
        env_path = Path(args.env) if args.env else None
        config_manager.initialize(config_path=config_path, env_path=env_path)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize configuration: {e}", file=sys.stderr)
        sys.exit(1)

    settings = config_manager.settings

    # 2. Configure logging
    try:
        configure_logging(settings)
    except Exception as e:
        print(f"CRITICAL: Failed to configure logging system: {e}", file=sys.stderr)
        sys.exit(1)

    logger = get_logger("NIDS.runner")
    logger.info("==================================================")
    logger.info("Initializing %s (v%s)", settings.project.name, settings.project.version)
    logger.info("Running in Environment: %s", settings.app_env.upper())
    logger.info("Execution Mode Selected: %s", args.mode.upper())
    logger.info("==================================================")

    # 3. Ensure necessary directories exist
    try:
        ensure_directory(settings.paths.raw_data_dir)
        ensure_directory(settings.paths.processed_data_dir)
        ensure_directory(settings.paths.external_data_dir)
        ensure_directory(settings.paths.models_dir)
        ensure_directory(settings.paths.logs_dir)
        logger.debug("Successfully validated directory structures.")
    except Exception as e:
        logger.exception("Failed to prepare directory structure: %s", e)
        sys.exit(1)

    # 4. Pipeline Execution
    try:
        if args.mode == "train":
            logger.info("Starting model training pipeline orchestration...")
            # ML code is not generated yet, placeholder log
            logger.info("Pipeline completed successfully (Dry Run).")
        elif args.mode == "predict":
            logger.info("Starting batch inference pipeline orchestration...")
            # ML code is not generated yet, placeholder log
            logger.info("Pipeline completed successfully (Dry Run).")
    except NIDSException as nids_err:
        logger.error("NIDS Specific Execution Failure: %s", nids_err)
        sys.exit(1)
    except Exception as general_err:
        logger.critical("Unexpected System Failure: %s", general_err, exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
