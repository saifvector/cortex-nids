"""
Unit tests for DataLoader, DataValidator, EDAAnalyzer, Visualizer, and ReportGenerator.
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from src.data_loader import DataLoader
from src.data_validator import DataValidator
from src.eda import EDAAnalyzer
from src.visualization import Visualizer
from src.report_generator import ReportGenerator, REPORTLAB_AVAILABLE


@pytest.fixture
def sample_csv_data(tmp_path):
    """Fixture to generate a mock network traffic CSV file for tests."""
    csv_file_1 = tmp_path / "Traffic_Day1.csv"
    csv_file_2 = tmp_path / "Traffic_Day2.csv"
    
    # 6 rows, some duplicates, infinities, and missing values
    data_1 = {
        " Destination Port": [80, 443, 80, 22, 443, 80],
        " Flow Duration": [100.0, 200.0, 150.0, 10.0, 300.0, 100.0],
        " Total Fwd Packets": [2, 4, 3, 1, 5, 2],
        "Flow Bytes/s": [2000.0, 4000.0, np.inf, 100.0, np.nan, 2000.0],
        " Label": ["BENIGN", "DDoS", "BENIGN", "PortScan", "DDoS", "BENIGN"]
    }
    
    # Aligned columns for day 2
    data_2 = {
        " Destination Port": [80, 21],
        " Flow Duration": [120.0, 5.0],
        " Total Fwd Packets": [3, 1],
        "Flow Bytes/s": [3000.0, 50.0],
        " Label": ["BENIGN", "PortScan"]
    }
    
    pd.DataFrame(data_1).to_csv(csv_file_1, index=False)
    pd.DataFrame(data_2).to_csv(csv_file_2, index=False)
    return [csv_file_1, csv_file_2]


def test_data_loader_scan_and_merge(sample_csv_data):
    """Verify that DataLoader scans, validates column headers, and merges CSVs."""
    loader = DataLoader(target_column="Label")
    
    # Scan directory
    files = loader.scan_raw_directory(sample_csv_data[0].parent)
    assert len(files) == 2
    
    # Load and merge
    merged_df = loader.load_and_merge(files)
    # Total combined rows: 6 + 2 = 8. Columns: 5
    assert merged_df.shape == (8, 5)
    assert "Flow Duration" in merged_df.columns
    assert " Destination Port" not in merged_df.columns  # Column names should be stripped


def test_data_loader_column_mismatch(tmp_path):
    """Verify that DataLoader raises DataPreprocessingError if columns do not align."""
    file_1 = tmp_path / "day1.csv"
    file_2 = tmp_path / "day2.csv"
    
    pd.DataFrame({"colA": [1, 2], "colB": [3, 4]}).to_csv(file_1, index=False)
    pd.DataFrame({"colA": [1, 2], "colC": [3, 4]}).to_csv(file_2, index=False)
    
    loader = DataLoader()
    with pytest.raises(Exception):
        loader.load_and_merge([file_1, file_2])


def test_data_loader_cleaning(sample_csv_data):
    """Verify duplicates, infinity, and NaN values cleaning."""
    loader = DataLoader(target_column="Label")
    raw_df = loader.load_and_merge(sample_csv_data)
    
    # Clean issues (should remove 1 duplicate row from Day1, replace inf, and impute NaN)
    cleaned_df = loader.clean_obvious_issues(raw_df)
    
    # Combined: 8 rows. Row 5 is duplicate of Row 0. So remaining: 7 rows.
    assert cleaned_df.shape == (7, 5)
    
    # Ensure infinity is gone
    assert not np.isinf(cleaned_df["Flow Bytes/s"]).any()
    
    # Ensure missing values are imputed
    assert not cleaned_df["Flow Bytes/s"].isnull().any()


def test_data_validator(sample_csv_data):
    """Verify that DataValidator audits dataset quality metrics."""
    loader = DataLoader(target_column="Label")
    raw_df = loader.load_and_merge(sample_csv_data)
    
    validator = DataValidator(target_column="Label")
    report = validator.run_validation(raw_df)
    
    assert report["dimensions"]["rows"] == 8
    assert report["dimensions"]["cols"] == 5
    assert report["duplicate_rows"]["count"] == 1
    assert report["infinite_values"]["total_count"] == 1
    assert "Flow Bytes/s" in report["missing_values"]["by_column_count"]
    assert report["memory_usage"]["total_mb"] > 0.0


def test_eda_analyzer(sample_csv_data):
    """Verify that EDAAnalyzer compiles statistics and correlations."""
    loader = DataLoader(target_column="Label")
    raw_df = loader.load_and_merge(sample_csv_data)
    cleaned_df = loader.clean_obvious_issues(raw_df)
    
    analyzer = EDAAnalyzer(target_column="Label")
    eda_report = analyzer.analyze(cleaned_df)
    
    # 7 rows remaining after duplicates dropped
    assert eda_report["shape"]["rows"] == 7
    assert len(eda_report["columns"]) == 5
    assert "Label" in eda_report["dtypes"]
    
    # Target class counts (BENIGN: 4, DDoS: 2, PortScan: 2. Wait: Day 1: BENIGN=3, DDoS=2, PortScan=1. Day 2: BENIGN=1, PortScan=1.
    # Total combined: BENIGN=4, DDoS=2, PortScan=2. Since 1 duplicate BENIGN from Day 1 was dropped: BENIGN=3, DDoS=2, PortScan=2. Total 7.
    # Let's inspect values:
    labels = [item["class"] for item in eda_report["target_distribution"]]
    assert "BENIGN" in labels
    assert "DDoS" in labels
    assert "PortScan" in labels
    
    # Verify Pearson/Spearman matrix are computed
    assert "pearson_matrix" in eda_report["correlations"]
    assert "spearman_matrix" in eda_report["correlations"]


def test_report_generation(sample_csv_data, tmp_path):
    """Verify that ReportGenerator outputs files in HTML and PDF formats."""
    loader = DataLoader(target_column="Label")
    raw_df = loader.load_and_merge(sample_csv_data)
    cleaned_df = loader.clean_obvious_issues(raw_df)
    
    validator = DataValidator(target_column="Label")
    val_report = validator.run_validation(cleaned_df)
    
    analyzer = EDAAnalyzer(target_column="Label")
    eda_report = analyzer.analyze(cleaned_df)
    
    # Save plots
    reports_dir = tmp_path / "reports"
    visualizer = Visualizer(output_dir=reports_dir)
    
    plots_b64 = {}
    plots_paths = {}
    
    plots_paths["class_distribution"] = reports_dir / "class_distribution.png"
    plots_b64["class_distribution"] = visualizer.plot_class_distribution(cleaned_df["Label"])
    
    plots_paths["correlation_heatmap_pearson"] = reports_dir / "correlation_heatmap_pearson.png"
    plots_b64["correlation_heatmap_pearson"] = visualizer.plot_correlation_heatmap(
        eda_report["correlations"]["pearson_matrix"], "Pearson"
    )
    
    plots_paths["missing_value_heatmap"] = reports_dir / "missing_values_heatmap.png"
    plots_b64["missing_value_heatmap"] = visualizer.plot_missing_value_heatmap(cleaned_df)

    plots_paths["boxplots"] = reports_dir / "boxplots.png"
    plots_b64["boxplots"] = visualizer.plot_boxplots(cleaned_df, ["Flow Duration"])

    # Instantiate generator
    report_gen = ReportGenerator(target_column="Label")
    
    # 1. Test CSV Exporter
    report_gen.save_csv_summaries(val_report, eda_report, reports_dir)
    assert (reports_dir / "feature_statistics.csv").exists()
    assert (reports_dir / "validation_summary.csv").exists()
    
    # 2. Test HTML compiler
    html_report = reports_dir / "eda_report.html"
    report_gen.generate_html_report(val_report, eda_report, plots_b64, html_report)
    assert html_report.exists()
    
    # 3. Test PDF Exporter
    if REPORTLAB_AVAILABLE:
        pdf_report = reports_dir / "eda_report.pdf"
        report_gen.generate_pdf_report(val_report, eda_report, plots_paths, pdf_report)
        assert pdf_report.exists()
