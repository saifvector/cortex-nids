"""
ReportGenerator module for NIDS.
Generates CSV summaries, print-ready HTML dashboards, and multi-page PDF documents
summarizing validation diagnostics and exploratory data analysis.
"""
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from src.exceptions.custom_exceptions import NIDSException
from src.utils.utils import ensure_directory, get_absolute_path

# Try-imports for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportGenerator:
    """
    OOP Report Generator. Exports data analysis results in CSV, HTML, and PDF formats.
    """

    def __init__(self, target_column: str = "Label"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column

    def save_csv_summaries(self, val_report: Dict[str, Any], eda_report: Dict[str, Any], output_dir: Union[str, Path]) -> None:
        """
        Saves tabular statistics into separate CSV files.
        """
        out_dir = get_absolute_path(output_dir)
        ensure_directory(out_dir)
        self.logger.info("Exporting CSV summaries to %s...", out_dir)

        try:
            # 1. Feature statistics
            if "feature_statistics" in eda_report:
                stats_df = pd.DataFrame(eda_report["feature_statistics"])
                stats_df.to_csv(out_dir / "feature_statistics.csv", index=False)

            # 2. Class distribution
            if "target_distribution" in eda_report:
                class_df = pd.DataFrame(eda_report["target_distribution"])
                class_df.to_csv(out_dir / "class_distribution.csv", index=False)

            # 3. Highly correlated features (Pearson)
            if "high_correlations_pearson" in eda_report:
                pearson_df = pd.DataFrame(eda_report["high_correlations_pearson"])
                pearson_df.to_csv(out_dir / "correlated_features_pearson.csv", index=False)

            # 4. Highly correlated features (Spearman)
            if "high_correlations_spearman" in eda_report:
                spearman_df = pd.DataFrame(eda_report["high_correlations_spearman"])
                spearman_df.to_csv(out_dir / "correlated_features_spearman.csv", index=False)

            # 5. Outliers
            if "outliers" in eda_report:
                out_list = []
                for col, info in eda_report["outliers"].items():
                    out_list.append({
                        "feature": col,
                        "outlier_count": info["count"],
                        "outlier_percentage": info["percentage"],
                        "q1": info["q1"],
                        "q3": info["q3"],
                        "iqr": info["iqr"]
                    })
                out_df = pd.DataFrame(out_list)
                out_df.to_csv(out_dir / "outliers_summary.csv", index=False)

            # 6. Validation details
            val_summary = {
                "metric": [
                    "total_rows", "total_columns", "duplicate_rows_count", "duplicate_rows_percentage",
                    "missing_values_count", "overall_null_percentage", "constant_features_count",
                    "duplicate_columns_count", "infinite_values_count", "memory_usage_mb"
                ],
                "value": [
                    val_report["dimensions"]["rows"],
                    val_report["dimensions"]["cols"],
                    val_report["duplicate_rows"]["count"],
                    val_report["duplicate_rows"]["percentage"],
                    val_report["missing_values"]["total_count"],
                    val_report["missing_values"]["overall_null_percentage"],
                    val_report["constant_features"]["count"],
                    len(val_report["duplicate_columns"]["by_content"]),
                    val_report["infinite_values"]["total_count"],
                    val_report["memory_usage"]["total_mb"]
                ]
            }
            pd.DataFrame(val_summary).to_csv(out_dir / "validation_summary.csv", index=False)
            self.logger.info("CSV summaries saved successfully.")

        except Exception as e:
            raise NIDSException(f"Failed to save CSV summaries: {e}") from e

    def generate_html_report(
        self, 
        val_report: Dict[str, Any], 
        eda_report: Dict[str, Any], 
        plots_b64: Dict[str, str], 
        output_path: Union[str, Path]
    ) -> Path:
        """
        Compiles and saves a comprehensive standalone HTML dashboard report.
        """
        report_file = get_absolute_path(output_path)
        ensure_directory(report_file.parent)
        self.logger.info("Compiling HTML report dashboard...")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shape = val_report["dimensions"]
        duplicates = val_report["duplicate_rows"]
        missing = val_report["missing_values"]
        
        # Determine statuses
        dup_status = "status-success" if duplicates["count"] == 0 else "status-warning"
        miss_status = "status-success" if missing["total_count"] == 0 else "status-warning"
        imb_status = "status-danger" if eda_report.get("class_imbalance_warning", False) else "status-success"
        empty_status = "status-success" if len(missing["empty_columns"]) == 0 else "status-danger"
        const_status = "status-success" if val_report["constant_features"]["count"] == 0 else "status-warning"

        # Missing values table
        missing_rows_html = ""
        if missing["by_column_count"]:
            # Sort by count descending
            sorted_missing = sorted(missing["by_column_count"].items(), key=lambda x: x[1], reverse=True)
            for col, count in sorted_missing[:12]:
                pct = missing["by_column_percentage"].get(col, 0.0)
                missing_rows_html += f"<tr><td>{col}</td><td>{count:,}</td><td>{pct:.3f}%</td></tr>"
            if len(sorted_missing) > 12:
                missing_rows_html += f"<tr><td colspan='3' class='text-center text-muted'>... and {len(sorted_missing) - 12} more columns. View validation_summary.csv</td></tr>"
        else:
            missing_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No missing values detected.</td></tr>"

        # Class distribution table
        class_rows_html = ""
        for item in eda_report.get("target_distribution", []):
            class_rows_html += f"<tr><td><strong>{item['class']}</strong></td><td>{item['count']:,}</td><td>{item['percentage']:.3f}%</td></tr>"

        # Outliers table rows
        outlier_rows_html = ""
        if "outliers" in eda_report:
            sorted_outliers = sorted(eda_report["outliers"].items(), key=lambda x: x[1]["count"], reverse=True)
            # Display top 10 outlier features
            for col, item in sorted_outliers[:10]:
                if item["count"] > 0:
                    outlier_rows_html += f"<tr><td>{col}</td><td>{item['count']:,}</td><td>{item['percentage']:.3f}%</td></tr>"
        if not outlier_rows_html:
            outlier_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No outliers detected in numerical columns.</td></tr>"

        # Correlated feature pairs
        corr_rows_html = ""
        high_corrs = eda_report.get("high_correlations_pearson", [])
        if high_corrs:
            for item in high_corrs[:10]:
                corr_rows_html += f"<tr><td>{item['feature_1']}</td><td>{item['feature_2']}</td><td class='text-center font-bold text-danger'>{item['coefficient']:.4f}</td></tr>"
        else:
            corr_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No highly correlated feature pairs found (&gt; 0.90).</td></tr>"

        # Duplicate columns list
        dup_cols_html = ""
        dup_cols = val_report["duplicate_columns"]["by_content"]
        if dup_cols:
            for pair in dup_cols:
                dup_cols_html += f"<tr><td><code>{pair[0]}</code></td><td><code>{pair[1]}</code></td><td class='text-center text-danger'>Duplicate Content</td></tr>"
        else:
            dup_cols_html = "<tr><td colspan='3' class='text-center text-muted'>No duplicate columns detected.</td></tr>"

        # Detailed stats table rows
        stats_rows_html = ""
        for feat in eda_report.get("feature_statistics", [])[:15]:
            stats_rows_html += f"""
            <tr>
                <td><strong>{feat['feature']}</strong></td>
                <td>{feat['mean']:.4e}</td>
                <td>{feat['std']:.4e}</td>
                <td>{feat['min']:.4e}</td>
                <td>{feat['50%']:.4e}</td>
                <td>{feat['max']:.4e}</td>
                <td>{feat['variance']:.4e}</td>
            </tr>
            """
        if len(eda_report.get("feature_statistics", [])) > 15:
            stats_rows_html += f"<tr><td colspan='7' class='text-center text-muted'>... and {len(eda_report['feature_statistics']) - 15} more features. View full details in feature_statistics.csv</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIDS Exploratory Data Analysis & Validation Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border-color: #e5e7eb;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            padding: 0;
        }}

        header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #1e1b4b 100%);
            color: white;
            padding: 30px 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
            letter-spacing: -0.5px;
        }}

        header p {{
            font-size: 14px;
            opacity: 0.8;
        }}

        .container {{
            max-width: 1300px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        .grid-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}

        .card-stat {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 5px solid var(--primary-light);
        }}

        .card-stat:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        }}

        .card-stat.warning-border {{ border-left-color: var(--warning); }}
        .card-stat.success-border {{ border-left-color: var(--success); }}
        .card-stat.danger-border {{ border-left-color: var(--danger); }}

        .card-stat .title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .card-stat .value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--text-main);
        }}

        .card-stat .subtitle {{
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 40px 0 20px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--border-color);
            color: var(--primary);
        }}

        .layout-split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 25px;
        }}

        @media (max-width: 900px) {{
            .layout-split {{
                grid-template-columns: 1fr;
            }}
        }}

        .card-box {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 25px;
        }}

        .card-box h3 {{
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 18px;
            color: var(--primary);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }}

        th {{
            background-color: #f9fafb;
            color: var(--text-main);
            font-weight: 600;
            font-size: 11px;
            text-align: left;
            padding: 10px 14px;
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 10px 14px;
            border-bottom: 1px solid var(--border-color);
            font-size: 12px;
        }}

        tr:hover td {{
            background-color: #f9fafb;
        }}

        .img-container {{
            width: 100%;
            text-align: center;
            margin: 15px 0;
        }}

        .img-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-success {{ background-color: #d1fae5; color: #065f46; }}
        .status-warning {{ background-color: #fef3c7; color: #92400e; }}
        .status-danger {{ background-color: #fee2e2; color: #991b1b; }}

        .font-bold {{ font-weight: 600; }}
        .text-center {{ text-align: center; }}
        .text-muted {{ color: var(--text-muted); }}
        .text-danger {{ color: var(--danger); }}

        footer {{
            background-color: #111827;
            color: #9ca3af;
            text-align: center;
            padding: 30px;
            font-size: 11px;
            margin-top: 50px;
        }}
    </style>
</head>
<body>

    <header>
        <h1>Dataset Validation & EDA Dashboard</h1>
        <p>Production Telemetry Diagnostic Report • Compiled at {timestamp}</p>
    </header>

    <div class="container">
        
        <!-- Summary Cards -->
        <div class="grid-summary">
            <div class="card-stat">
                <div class="title">Total Rows</div>
                <div class="value">{shape['rows']:,}</div>
                <div class="subtitle">Loaded flow records</div>
            </div>
            <div class="card-stat">
                <div class="title">Total Columns</div>
                <div class="value">{shape['cols']:,}</div>
                <div class="subtitle">Dimensions parsed</div>
            </div>
            <div class="card-stat {dup_status}-border">
                <div class="title">Duplicate Rows</div>
                <div class="value">{duplicates['percentage']:.2f}%</div>
                <div class="subtitle">{duplicates['count']:,} rows</div>
            </div>
            <div class="card-stat {miss_status}-border">
                <div class="title">Null Elements</div>
                <div class="value">{missing['overall_null_percentage']:.4f}%</div>
                <div class="subtitle">{missing['total_count']:,} elements</div>
            </div>
            <div class="card-stat {imb_status}-border">
                <div class="title">Imbalance Warn</div>
                <div class="value">
                    <span class="badge {imb_status}">
                        {"WARNING" if eda_report.get('class_imbalance_warning', False) else "OK"}
                    </span>
                </div>
                <div class="subtitle">Min Class: {eda_report.get('min_class_percentage', 0.0):.2f}%</div>
            </div>
            <div class="card-stat">
                <div class="title">Memory Usage</div>
                <div class="value">{val_report['memory_usage']['total_mb']:.2f} MB</div>
                <div class="subtitle">Memory allocation size</div>
            </div>
        </div>

        <div class="section-title">NIDS Dataset Quality Assessment</div>
        
        <div class="layout-split">
            <div class="card-box">
                <h3>Empty & Constant Columns Integrity Check</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Metric Audit</th>
                            <th>Count</th>
                            <th>Status Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Empty Columns</strong> (All Null)</td>
                            <td>{len(missing['empty_columns'])}</td>
                            <td>
                                <span class="badge {empty_status}">
                                    {"ALERT" if len(missing['empty_columns']) > 0 else "PASS"}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Constant Features</strong> (0 Variance)</td>
                            <td>{val_report['constant_features']['count']}</td>
                            <td>
                                <span class="badge {const_status}">
                                    {"REVIEW" if val_report['constant_features']['count'] > 0 else "PASS"}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Infinite Values</strong> (inf / -inf)</td>
                            <td>{val_report['infinite_values']['total_count']}</td>
                            <td>
                                <span class="badge {'status-warning' if val_report['infinite_values']['total_count'] > 0 else 'status-success'}">
                                    {val_report['infinite_values']['total_count']} detected
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Mixed Datatypes</strong> (Strings inside numeric cols)</td>
                            <td>{len(val_report['invalid_numeric_values']['by_column'])}</td>
                            <td>
                                <span class="badge {'status-warning' if len(val_report['invalid_numeric_values']['by_column']) > 0 else 'status-success'}">
                                    {len(val_report['invalid_numeric_values']['by_column'])} cols
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <h3 style="margin-top: 30px;">Duplicate Features Check</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Feature Name 1</th>
                            <th>Feature Name 2</th>
                            <th class="text-center">Relation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {dup_cols_html}
                    </tbody>
                </table>
            </div>

            <div class="card-box">
                <h3>Missing values by Column (Top 12)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Variable Name</th>
                            <th>Null Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {missing_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card-box">
            <h3>Dataset Missingness Grid Overview</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{plots_b64.get('missing_value_heatmap', '')}" alt="Missing Value Heatmap">
            </div>
        </div>

        <div class="section-title">Target Variable Analysis</div>

        <div class="layout-split">
            <div class="card-box">
                <h3>Class Distribution Detail</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Traffic Label / Category</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {class_rows_html}
                    </tbody>
                </table>
            </div>

            <div class="card-box">
                <h3>Target Distributions Chart</h3>
                <div class="img-container">
                    <img src="data:image/png;base64,{plots_b64.get('class_distribution', '')}" alt="Class Distribution Bar Chart">
                </div>
            </div>
        </div>

        <div class="section-title">Statistical Feature Correlation</div>

        <div class="layout-split">
            <div class="card-box">
                <h3>Pearson Heatmap (Top 12 by Variance)</h3>
                <div class="img-container">
                    <img src="data:image/png;base64,{plots_b64.get('correlation_heatmap_pearson', '')}" alt="Pearson Correlation Heatmap">
                </div>
            </div>
            <div class="card-box">
                <h3>Spearman Heatmap (Top 12 by Variance)</h3>
                <div class="img-container">
                    <img src="data:image/png;base64,{plots_b64.get('correlation_heatmap_spearman', '')}" alt="Spearman Correlation Heatmap">
                </div>
            </div>
        </div>

        <div class="card-box">
            <h3>Highly Correlated Multicollinearity Pairs (Pearson &gt; {0.90:.2f})</h3>
            <table>
                <thead>
                    <tr>
                        <th>Feature 1</th>
                        <th>Feature 2</th>
                        <th class="text-center">Pearson r</th>
                    </tr>
                </thead>
                <tbody>
                    {corr_rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-title">Distribution & Outlier Diagnostics</div>

        <div class="layout-split">
            <div class="card-box">
                <h3>Outliers Summary (IQR Method - Top 10)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Feature Name</th>
                            <th>Outliers Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {outlier_rows_html}
                    </tbody>
                </table>
            </div>
            <div class="card-box">
                <h3>Boxplots Grid</h3>
                <div class="img-container" style="margin-top: -15px;">
                    <img src="data:image/png;base64,{plots_b64.get('boxplots', '')}" alt="Outliers Boxplots Grid">
                </div>
            </div>
        </div>

        <div class="card-box">
            <h3>Feature Histograms Grid</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{plots_b64.get('histograms', '')}" alt="Histograms Grid">
            </div>
        </div>

        <div class="card-box">
            <h3>Feature Density Plots Grid</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{plots_b64.get('density_plots', '')}" alt="Density Plots Grid">
            </div>
        </div>

        <div class="card-box">
            <h3>Overlay Distributions: Benign vs Malicious</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{plots_b64.get('feature_distributions_split', '')}" alt="Split KDE Distributions Grid">
            </div>
        </div>

        <div class="section-title">Feature Statistics details</div>

        <div class="card-box" style="overflow-x: auto;">
            <h3>Numerical Features Statistics Summary (Top 15 sorted by variance)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Median</th>
                        <th>Max</th>
                        <th>Variance</th>
                    </tr>
                </thead>
                <tbody>
                    {stats_rows_html}
                </tbody>
            </table>
        </div>

    </div>

    <footer>
        <p>&copy; 2026 NIDS. All Rights Reserved. Production ML Architecture.</p>
    </footer>

</body>
</html>
"""
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info("HTML report successfully generated at: %s", report_file)
            return report_file
        except Exception as e:
            raise NIDSException(f"Failed to write HTML report: {e}") from e

    def generate_pdf_report(
        self, 
        val_report: Dict[str, Any], 
        eda_report: Dict[str, Any], 
        plots_paths: Dict[str, Path], 
        output_path: Union[str, Path]
    ) -> Optional[Path]:
        """
        Compiles a multi-page PDF document reporting NIDS quality analysis.
        Uses reportlab Platypus templates.
        """
        pdf_file = get_absolute_path(output_path)
        ensure_directory(pdf_file.parent)

        if not REPORTLAB_AVAILABLE:
            self.logger.warning("Reportlab library is not installed/functional. Skipping PDF report generation.")
            return None

        self.logger.info("Compiling PDF report at: %s...", pdf_file)
        try:
            # 1. Setup Document Template
            doc = SimpleDocTemplate(
                str(pdf_file),
                pagesize=letter,
                rightMargin=0.5*inch, leftMargin=0.5*inch,
                topMargin=0.5*inch, bottomMargin=0.5*inch
            )

            # 2. Setup styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                "PDFTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                textColor=colors.HexColor("#1e3a8a"),
                spaceAfter=10
            )
            
            subtitle_style = ParagraphStyle(
                "PDFSubTitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=12,
                textColor=colors.HexColor("#6b7280"),
                spaceAfter=25
            )

            h1_style = ParagraphStyle(
                "PDFH1",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#1e3a8a"),
                spaceBefore=15,
                spaceAfter=10
            )

            h2_style = ParagraphStyle(
                "PDFH2",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=14,
                textColor=colors.HexColor("#1e3a8a"),
                spaceBefore=10,
                spaceAfter=8
            )

            body_style = ParagraphStyle(
                "PDFBody",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#1f2937"),
                spaceAfter=8
            )

            table_body_style = ParagraphStyle(
                "PDFTableBody",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#1f2937")
            )
            
            table_header_style = ParagraphStyle(
                "PDFTableHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=colors.white
            )

            story = []

            # ==================== PAGE 1: TITLE & SUMMARY ====================
            story.append(Paragraph("Dataset Validation & EDA Report", title_style))
            story.append(Paragraph(f"Machine Learning-Based Network Intrusion Detection System • Compiled at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
            
            story.append(Paragraph("1. Executive Summary & Base Dimensions", h1_style))
            summary_text = (
                "This report outlines the structural parameters and data quality profile "
                "of the loaded network telemetry flow records. Automated validation and exploratory "
                "analyses were run to prepare the features for machine learning pipelines."
            )
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 10))

            # General stats table
            shape = val_report["dimensions"]
            duplicates = val_report["duplicate_rows"]
            missing = val_report["missing_values"]
            
            summary_data = [
                [Paragraph("Quality Diagnostic Metric", table_header_style), Paragraph("Value Detail", table_header_style)],
                [Paragraph("Total Dataset Rows", table_body_style), Paragraph(f"{shape['rows']:,}", table_body_style)],
                [Paragraph("Total Dataset Columns", table_body_style), Paragraph(f"{shape['cols']:,}", table_body_style)],
                [Paragraph("Duplicate Rows Count", table_body_style), Paragraph(f"{duplicates['count']:,}", table_body_style)],
                [Paragraph("Duplicate Rows Percentage", table_body_style), Paragraph(f"{duplicates['percentage']:.2f}%", table_body_style)],
                [Paragraph("Missing Value Entries Count", table_body_style), Paragraph(f"{missing['total_count']:,}", table_body_style)],
                [Paragraph("Overall Null Percentage", table_body_style), Paragraph(f"{missing['overall_null_percentage']:.4f}%", table_body_style)],
                [Paragraph("Empty Columns Count", table_body_style), Paragraph(f"{len(missing['empty_columns'])}", table_body_style)],
                [Paragraph("Constant Columns Count (0 Variance)", table_body_style), Paragraph(f"{val_report['constant_features']['count']}", table_body_style)],
                [Paragraph("Infinite Values Count", table_body_style), Paragraph(f"{val_report['infinite_values']['total_count']}", table_body_style)],
                [Paragraph("Memory Usage Size", table_body_style), Paragraph(f"{val_report['memory_usage']['total_mb']:.2f} MB", table_body_style)],
            ]

            t_summary = Table(summary_data, colWidths=[2.5*inch, 4.0*inch])
            t_summary.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#1e3a8a")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ]))
            story.append(t_summary)
            story.append(PageBreak())

            # ==================== PAGE 2: TARGET CLASS DISTRIBUTION ====================
            story.append(Paragraph("2. Target Variable & Class Distribution", h1_style))
            story.append(Paragraph("Details the frequency breakdown and relative ratios of Benign vs Attack category labels.", body_style))
            story.append(Spacer(1, 10))

            # Class table
            class_data = [[Paragraph("Traffic Category Label", table_header_style), Paragraph("Record Count", table_header_style), Paragraph("Percentage", table_header_style)]]
            for item in eda_report.get("target_distribution", []):
                class_data.append([
                    Paragraph(f"<b>{item['class']}</b>", table_body_style),
                    Paragraph(f"{item['count']:,}", table_body_style),
                    Paragraph(f"{item['percentage']:.3f}%", table_body_style)
                ])
            
            t_class = Table(class_data, colWidths=[2.5*inch, 2.0*inch, 2.0*inch])
            t_class.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ]))
            story.append(t_class)
            story.append(Spacer(1, 15))

            # Class Distribution Plot
            if "class_distribution" in plots_paths and plots_paths["class_distribution"].exists():
                story.append(RLImage(str(plots_paths["class_distribution"]), width=6.5*inch, height=3.8*inch))

            story.append(PageBreak())

            # ==================== PAGE 3: DATA QUALITY AUDIT ====================
            story.append(Paragraph("3. Missing Values Heatmap Grid Analysis", h1_style))
            story.append(Paragraph("Shows the missing value distributions across top variables containing null values.", body_style))
            story.append(Spacer(1, 10))

            if "missing_value_heatmap" in plots_paths and plots_paths["missing_value_heatmap"].exists():
                story.append(RLImage(str(plots_paths["missing_value_heatmap"]), width=6.5*inch, height=3.8*inch))
                
            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Empty Columns Identified:</b>", h2_style))
            if missing["empty_columns"]:
                empty_text = ", ".join(missing["empty_columns"])
            else:
                empty_text = "None. All columns contain at least some non-null values."
            story.append(Paragraph(empty_text, body_style))

            story.append(Paragraph("<b>Constant Columns Identified (0 Variance):</b>", h2_style))
            if val_report["constant_features"]["columns"]:
                const_text = ", ".join(val_report["constant_features"]["columns"])
            else:
                const_text = "None. All columns exhibit non-zero variance."
            story.append(Paragraph(const_text, body_style))

            story.append(PageBreak())

            # ==================== PAGE 4: FEATURE CORRELATION ====================
            story.append(Paragraph("4. Heatmap Correlation Matrix Diagnostics", h1_style))
            story.append(Paragraph("Presents the Pearson correlation heatmap of features with highest variance to analyze multicollinearity.", body_style))
            story.append(Spacer(1, 10))

            if "correlation_heatmap_pearson" in plots_paths and plots_paths["correlation_heatmap_pearson"].exists():
                story.append(RLImage(str(plots_paths["correlation_heatmap_pearson"]), width=6.5*inch, height=4.5*inch))
                
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Highly Correlated Feature Pairs (Top 5):</b>", h2_style))
            
            corr_pairs = eda_report.get("high_correlations_pearson", [])
            if corr_pairs:
                corr_bullets = ""
                for pair in corr_pairs[:5]:
                    corr_bullets += f"• {pair['feature_1']} &lt;=&gt; {pair['feature_2']} : Pearson r = {pair['coefficient']:.4f}<br/>"
                story.append(Paragraph(corr_bullets, body_style))
            else:
                story.append(Paragraph("No highly correlated pairs above threshold found.", body_style))

            story.append(PageBreak())

            # ==================== PAGE 5: OUTLIERS DIAGNOSTIC ====================
            story.append(Paragraph("5. Outlier Distributions (Interquartile Range)", h1_style))
            story.append(Paragraph("Boxplots mapping distributions and outlier ranges for high-variance numerical features.", body_style))
            story.append(Spacer(1, 10))

            if "boxplots" in plots_paths and plots_paths["boxplots"].exists():
                story.append(RLImage(str(plots_paths["boxplots"]), width=6.5*inch, height=4.0*inch))

            story.append(Spacer(1, 15))
            story.append(Paragraph("<b>Outliers Statistics Table (Top 5):</b>", h2_style))
            
            out_data = [[Paragraph("Feature Name", table_header_style), Paragraph("Outliers Count", table_header_style), Paragraph("Percentage", table_header_style)]]
            sorted_outliers = sorted(eda_report.get("outliers", {}).items(), key=lambda x: x[1]["count"], reverse=True)
            
            for col, item in sorted_outliers[:5]:
                if item["count"] > 0:
                    out_data.append([
                        Paragraph(col, table_body_style),
                        Paragraph(f"{item['count']:,}", table_body_style),
                        Paragraph(f"{item['percentage']:.3f}%", table_body_style)
                    ])

            if len(out_data) > 1:
                t_out = Table(out_data, colWidths=[3.0*inch, 1.8*inch, 1.7*inch])
                t_out.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ]))
                story.append(t_out)

            # 3. Build document
            doc.build(story)
            self.logger.info("PDF report compiled successfully at: %s", pdf_file)
            return pdf_file

        except Exception as e:
            self.logger.exception("Failed to compile PDF report: %s", e)
            return None
