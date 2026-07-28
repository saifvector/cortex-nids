#!/usr/bin/env python
"""
Main pipeline execution script for NIDS Data Loading, Validation, Clean, and EDA.
Merges CSV files, validates structures, cleans obvious issues (retaining attack records),
executes EDA profiling, plots statistics, and outputs CSV summaries, print-ready HTML,
and PDF reports inside reports/eda/.
"""
import sys
import logging
from pathlib import Path

# Add project root to system paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.config import ConfigManager
from src.utils.logging import configure_logging, get_logger
from src.utils.utils import ensure_directory, get_absolute_path
from src.data_loader import DataLoader
from src.data_validator import DataValidator
from src.eda import EDAAnalyzer
from src.visualization import Visualizer
from src.report_generator import ReportGenerator


def main():
    # 1. Boot up configurations and logging
    config_manager = ConfigManager()
    config_manager.initialize()
    settings = config_manager.settings

    configure_logging(settings)
    logger = get_logger("NIDS.eda_pipeline")

    logger.info("==================================================")
    logger.info("NIDS Data Loader & Comprehensive EDA Pipeline Run")
    logger.info("==================================================")

    # Resolve folder paths from settings
    raw_data_dir = get_absolute_path(settings.paths.raw_data_dir)
    processed_dir = get_absolute_path(settings.paths.processed_data_dir)
    reports_dir = get_absolute_path("reports/eda")

    ensure_directory(raw_data_dir)
    ensure_directory(processed_dir)
    ensure_directory(reports_dir)

    target_col = settings.data_preparation.target_column

    # 2. Automatically Scan & Load Raw CSVs
    loader = DataLoader(target_column=target_col)
    try:
        csv_files = loader.scan_raw_directory(raw_data_dir)
        raw_df = loader.load_and_merge(csv_files)
    except Exception as e:
        logger.critical("Failed to load and merge raw datasets: %s", e, exc_info=True)
        sys.exit(1)

    # 3. Clean obvious issues (Remove duplicates, replace infs, handle NaNs safely)
    # We save this to data/processed/merged_dataset.csv as requested
    try:
        cleaned_df = loader.clean_obvious_issues(
            raw_df, 
            impute_strategy=settings.data_preparation.imputation_strategy
        )
        target_col = loader.target_column
        cleaned_dataset_path = processed_dir / "merged_dataset.csv"
        loader.save_processed_data(cleaned_df, cleaned_dataset_path)
    except Exception as e:
        logger.critical("Failed during dataset cleaning and saving phase: %s", e, exc_info=True)
        sys.exit(1)

    # 4. Perform Data Validation
    validator = DataValidator(target_column=target_col)
    try:
        validation_report = validator.run_validation(cleaned_df)
    except Exception as e:
        logger.critical("Failed during dataset validation check phase: %s", e, exc_info=True)
        sys.exit(1)

    # 5. Perform Exploratory Data Analysis
    analyzer = EDAAnalyzer(target_column=target_col)
    try:
        # Load correlation threshold from config if available (default to 0.90)
        eda_report = analyzer.analyze(cleaned_df, correlation_threshold=0.90)
    except Exception as e:
        logger.critical("Failed during Exploratory Data Analysis phase: %s", e, exc_info=True)
        sys.exit(1)

    # 6. Generate and Save Plots
    visualizer = Visualizer(output_dir=reports_dir)
    plots_b64 = {}
    plots_paths = {}

    try:
        # Get key features with highest variance to display on grids
        stats_list = eda_report["feature_statistics"]
        key_features = [s["feature"] for s in stats_list if s["variance"] > 1e-5][:6]
        logger.info("Selected top features for detailed plotting: %s", key_features)

        # Generate plots
        # Save plots to disk and cache Base64 representation
        plots_paths["class_distribution"] = reports_dir / "class_distribution.png"
        plots_b64["class_distribution"] = visualizer.plot_class_distribution(
            cleaned_df[target_col], 
            filename="class_distribution.png"
        )

        plots_paths["correlation_heatmap_pearson"] = reports_dir / "correlation_heatmap_pearson.png"
        plots_b64["correlation_heatmap_pearson"] = visualizer.plot_correlation_heatmap(
            eda_report["correlations"]["pearson_matrix"],
            method_name="Pearson",
            top_n=12,
            filename="correlation_heatmap_pearson.png"
        )

        plots_paths["correlation_heatmap_spearman"] = reports_dir / "correlation_heatmap_spearman.png"
        plots_b64["correlation_heatmap_spearman"] = visualizer.plot_correlation_heatmap(
            eda_report["correlations"]["spearman_matrix"],
            method_name="Spearman",
            top_n=12,
            filename="correlation_heatmap_spearman.png"
        )

        plots_paths["histograms"] = reports_dir / "histograms.png"
        plots_b64["histograms"] = visualizer.plot_histograms(
            cleaned_df, 
            features=key_features[:6], 
            filename="histograms.png"
        )

        plots_paths["boxplots"] = reports_dir / "boxplots.png"
        plots_b64["boxplots"] = visualizer.plot_boxplots(
            cleaned_df, 
            features=key_features[:6], 
            filename="boxplots.png"
        )

        plots_paths["density_plots"] = reports_dir / "density_plots.png"
        plots_b64["density_plots"] = visualizer.plot_density_plots(
            cleaned_df, 
            features=key_features[:6], 
            filename="density_plots.png"
        )

        plots_paths["feature_distributions_split"] = reports_dir / "feature_distributions_split.png"
        plots_b64["feature_distributions_split"] = visualizer.plot_feature_distributions(
            cleaned_df,
            features=key_features[:4],
            target_col=target_col,
            filename="feature_distributions_split.png"
        )

        plots_paths["missing_value_heatmap"] = reports_dir / "missing_values_heatmap.png"
        plots_b64["missing_value_heatmap"] = visualizer.plot_missing_value_heatmap(
            cleaned_df,
            filename="missing_values_heatmap.png"
        )

    except Exception as e:
        logger.critical("Failed during visualizations rendering phase: %s", e, exc_info=True)
        sys.exit(1)

    # 7. Generate and Save Reports
    report_gen = ReportGenerator(target_column=target_col)
    try:
        # Save CSV summaries
        report_gen.save_csv_summaries(validation_report, eda_report, reports_dir)

        # Save HTML report
        html_report_path = reports_dir / "eda_report.html"
        report_gen.generate_html_report(validation_report, eda_report, plots_b64, html_report_path)

        # Save PDF report
        pdf_report_path = reports_dir / "eda_report.pdf"
        report_gen.generate_pdf_report(validation_report, eda_report, plots_paths, pdf_report_path)

        logger.info("==================================================")
        logger.info("Pipeline Complete. Data cleaned, plots saved, reports written.")
        logger.info("Processed CSV: %s", cleaned_dataset_path.resolve())
        logger.info("HTML Report:   %s", html_report_path.resolve())
        logger.info("PDF Report:    %s", pdf_report_path.resolve())
        logger.info("==================================================")

    except Exception as e:
        logger.critical("Failed during final report generation phase: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
