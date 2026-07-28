"""
Exploratory Data Analysis (EDA) module for NIDS.
Calculates statistical metrics (shapes, missing values, duplicates, class imbalance, outliers, correlations),
invokes the Visualizer to render plots, and compiles a comprehensive self-contained HTML EDA report.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import NIDSException, ConfigurationError
from src.utils.visualization import Visualizer
from src.utils.utils import ensure_directory, get_absolute_path


class EDAAnalyzer:
    """
    OOP analyzer to extract statistics, detect anomalies (outliers, duplicates),
    and build a beautifully formatted standalone HTML report.
    """

    def __init__(self, target_column: str = "label"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes a comprehensive statistical profiling of the dataframe:
        - shape and datatypes counts
        - missing values and duplicates
        - class balance distribution
        - statistics for numerical columns
        - outlier calculation (IQR method)
        - highly correlated pairs
        """
        self.logger.info("Starting dataset profiling...")
        results = {}

        # 1. Base Dimensions
        num_rows, num_cols = df.shape
        results["shape"] = {"rows": num_rows, "cols": num_cols}

        # 2. Datatypes Counts
        dt_counts = df.dtypes.value_counts()
        results["dtypes"] = {str(k): int(v) for k, v in dt_counts.items()}

        # 3. Duplicate Records
        dup_count = int(df.duplicated().sum())
        results["duplicates"] = {
            "count": dup_count,
            "percentage": (dup_count / num_rows * 100) if num_rows > 0 else 0
        }

        # 4. Missing Values
        null_counts = df.isnull().sum()
        total_nulls = int(null_counts.sum())
        results["missing_values"] = {
            "total_count": total_nulls,
            "percentage": (total_nulls / (num_rows * num_cols) * 100) if num_rows > 0 and num_cols > 0 else 0,
            "by_column": {col: int(val) for col, val in null_counts.items() if val > 0}
        }

        # 5. Class Balance
        if self.target_column in df.columns:
            class_counts = df[self.target_column].value_counts()
            class_pct = df[self.target_column].value_counts(normalize=True) * 100
            results["class_distribution"] = [
                {
                    "class": str(label),
                    "count": int(count),
                    "percentage": float(class_pct[label])
                }
                for label, count in class_counts.items()
            ]
            
            # Simple heuristic check for imbalance
            min_class_pct = class_pct.min()
            results["class_imbalance_warning"] = bool(min_class_pct < 5.0)  # Warning if any class is < 5% of dataset
        else:
            results["class_distribution"] = []
            results["class_imbalance_warning"] = False

        # 6. Feature statistics & Outliers (using IQR)
        # Select numeric columns
        num_cols_df = df.select_dtypes(include=[np.number])
        outliers_summary = {}
        feature_stats = []

        self.logger.debug("Calculating IQR outlier limits and feature statistics...")
        for col in num_cols_df.columns:
            if col == self.target_column:
                continue
                
            q1 = num_cols_df[col].quantile(0.25)
            q3 = num_cols_df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_mask = (num_cols_df[col] < lower_bound) | (num_cols_df[col] > upper_bound)
            col_outliers = int(outlier_mask.sum())
            
            outliers_summary[col] = {
                "count": col_outliers,
                "percentage": (col_outliers / num_rows * 100) if num_rows > 0 else 0
            }

            # Feature statistics
            feature_stats.append({
                "feature": col,
                "mean": float(num_cols_df[col].mean()),
                "std": float(num_cols_df[col].std()) if num_rows > 1 else 0.0,
                "min": float(num_cols_df[col].min()),
                "median": float(num_cols_df[col].median()),
                "max": float(num_cols_df[col].max()),
                "outliers_count": col_outliers,
                "variance": float(num_cols_df[col].var()) if num_rows > 1 else 0.0
            })

        results["outliers"] = outliers_summary
        results["feature_statistics"] = feature_stats

        # 7. Highly Correlated Feature Pairs (> 0.90)
        self.logger.debug("Identifying high correlation feature pairs...")
        high_corr_pairs = []
        if not num_cols_df.empty and num_cols_df.shape[1] > 1:
            # Drop labels if numeric
            corr_df = num_cols_df.drop(columns=[self.target_column]) if self.target_column in num_cols_df.columns else num_cols_df
            corr_matrix = corr_df.corr().abs()
            
            # Select upper triangle
            upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            
            # Find pairs with correlation > 0.90
            for col_name in upper_tri.columns:
                high_corr = upper_tri[col_name][upper_tri[col_name] > 0.90]
                for row_name, val in high_corr.items():
                    high_corr_pairs.append({
                        "feature_1": str(row_name),
                        "feature_2": str(col_name),
                        "coefficient": float(val)
                    })
                    
        # Sort by coefficient descending
        high_corr_pairs = sorted(high_corr_pairs, key=lambda x: x["coefficient"], reverse=True)
        results["high_correlations"] = high_corr_pairs

        self.logger.info("Dataset profiling completed.")
        return results

    def _select_key_features(self, df: pd.DataFrame, stats: List[Dict[str, Any]], count: int = 6) -> List[str]:
        """
        Heuristically selects top features to plot in grid summaries.
        Prioritizes features with non-zero variance and higher variance.
        """
        # Filter features with variance > 0
        valid_feats = [s for s in stats if s["variance"] > 1e-5 and s["feature"] != self.target_column]
        if not valid_feats:
            # Fallback to whatever numerical columns exist
            num_cols = df.select_dtypes(include=[np.number]).columns
            return [col for col in num_cols if col != self.target_column][:count]
            
        # Sort by variance descending
        sorted_feats = sorted(valid_feats, key=lambda x: x["variance"], reverse=True)
        return [s["feature"] for s in sorted_feats[:count]]

    def generate_html_report(self, df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
        """
        Coordinates profiling, plotting, and compiles a comprehensive HTML Report.
        """
        report_file = get_absolute_path(output_path)
        ensure_directory(report_file.parent)
        
        self.logger.info("Initiating automated report compilation...")

        # 1. Get statistics
        stats = self.analyze_dataset(df)

        # 2. Select key features for distributions
        key_features = self._select_key_features(df, stats["feature_statistics"], count=6)
        self.logger.info("Selected top features for detail plotting: %s", key_features)

        # 3. Create plots
        visualizer = Visualizer(output_dir=report_file.parent / "figures")
        
        # Plot and retrieve Base64 images
        b64_class = visualizer.plot_class_distribution(df[self.target_column]) if self.target_column in df.columns else ""
        b64_corr = visualizer.plot_correlation_matrix(df, top_n=12)
        b64_hist = visualizer.plot_histograms(df, key_features[:6])
        b64_box = visualizer.plot_boxplots(df, key_features[:6])
        b64_split = visualizer.plot_feature_distributions(df, key_features[:4], self.target_column)

        # 4. Render HTML template
        html_content = self._compile_template(stats, key_features, b64_class, b64_corr, b64_hist, b64_box, b64_split)

        # 5. Save report
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info("Report successfully generated at: %s", report_file)
            return report_file
        except Exception as e:
            raise NIDSException(f"Failed to save HTML report: {e}") from e

    def _compile_template(
        self, 
        stats: Dict[str, Any], 
        key_features: List[str],
        b64_class: str, 
        b64_corr: str, 
        b64_hist: str, 
        b64_box: str, 
        b64_split: str
    ) -> str:
        """
        Compiles the HTML template with stats and embedded Base64 charts.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shape = stats["shape"]
        duplicates = stats["duplicates"]
        missing = stats["missing_values"]
        class_dist = stats["class_distribution"]
        
        # Build status badges
        dup_status = "status-success" if duplicates["count"] == 0 else "status-warning"
        miss_status = "status-success" if missing["total_count"] == 0 else "status-warning"
        imb_status = "status-danger" if stats["class_imbalance_warning"] else "status-success"

        # Missing values rows
        missing_rows_html = ""
        if missing["by_column"]:
            for col, count in missing["by_column"].items():
                pct = (count / shape["rows"]) * 100
                missing_rows_html += f"<tr><td>{col}</td><td>{count:,}</td><td>{pct:.3f}%</td></tr>"
        else:
            missing_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No missing values detected.</td></tr>"

        # Class distribution rows
        class_rows_html = ""
        for item in class_dist:
            class_rows_html += f"<tr><td><strong>{item['class']}</strong></td><td>{item['count']:,}</td><td>{item['percentage']:.3f}%</td></tr>"

        # Correlated features rows
        corr_rows_html = ""
        if stats["high_correlations"]:
            # Display top 10 correlation pairs
            for item in stats["high_correlations"][:10]:
                corr_rows_html += f"<tr><td>{item['feature_1']}</td><td>{item['feature_2']}</td><td class='text-center font-bold text-danger'>{item['coefficient']:.4f}</td></tr>"
        else:
            corr_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No highly correlated features detected (&gt; 0.90).</td></tr>"

        # Outliers table rows
        outlier_rows_html = ""
        # Sort features by outlier count descending
        sorted_outliers = sorted(stats["outliers"].items(), key=lambda x: x[1]["count"], reverse=True)
        # Display top 10 outlier features
        for col, item in sorted_outliers[:10]:
            if item["count"] > 0:
                outlier_rows_html += f"<tr><td>{col}</td><td>{item['count']:,}</td><td>{item['percentage']:.3f}%</td></tr>"
        if not outlier_rows_html:
            outlier_rows_html = "<tr><td colspan='3' class='text-center text-muted'>No outliers detected in numerical columns.</td></tr>"

        # Feature stats table rows
        stats_rows_html = ""
        for feat in stats["feature_statistics"][:15]:  # show top 15 features
            stats_rows_html += f"""
            <tr>
                <td><strong>{feat['feature']}</strong></td>
                <td>{feat['mean']:.4e}</td>
                <td>{feat['std']:.4e}</td>
                <td>{feat['min']:.4e}</td>
                <td>{feat['median']:.4e}</td>
                <td>{feat['max']:.4e}</td>
                <td>{feat['outliers_count']:,}</td>
            </tr>
            """
        if len(stats["feature_statistics"]) > 15:
            stats_rows_html += f"<tr><td colspan='7' class='text-center text-muted'>... and {len(stats['feature_statistics'])-15} more features. View full details in configuration.</td></tr>"

        # Assemble HTML string
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIDS Exploratory Data Analysis Report</title>
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
            position: relative;
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
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card-stat {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 24px;
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
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .card-stat .value {{
            font-size: 26px;
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
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .layout-split {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
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
            margin-bottom: 35px;
        }}

        .card-box h3 {{
            font-size: 16px;
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
            font-size: 12px;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
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
        .text-right {{ text-align: right; }}
        .text-muted {{ color: var(--text-muted); }}
        .text-danger {{ color: var(--danger); }}

        footer {{
            background-color: #111827;
            color: #9ca3af;
            text-align: center;
            padding: 30px;
            font-size: 12px;
            margin-top: 50px;
        }}

        .badge-system {{
            font-size: 12px;
            padding: 4px 10px;
        }}
    </style>
</head>
<body>

    <header>
        <h1>Exploratory Data Analysis Report</h1>
        <p>NIDS Codebase Automated Diagnostic • Compiled at {timestamp}</p>
    </header>

    <div class="container">
        
        <!-- Summary Cards -->
        <div class="grid-summary">
            <div class="card-stat">
                <div class="title">Total Records</div>
                <div class="value">{shape['rows']:,}</div>
                <div class="subtitle">Packet flow telemetry samples</div>
            </div>
            <div class="card-stat">
                <div class="title">Total Columns</div>
                <div class="value">{shape['cols']:,}</div>
                <div class="subtitle">Dimensions/features captured</div>
            </div>
            <div class="card-stat {dup_status}-border">
                <div class="title">Duplicates</div>
                <div class="value">{duplicates['percentage']:.2f}%</div>
                <div class="subtitle">{duplicates['count']:,} duplicate rows</div>
            </div>
            <div class="card-stat {miss_status}-border">
                <div class="title">Missing Values</div>
                <div class="value">{missing['percentage']:.3f}%</div>
                <div class="subtitle">{missing['total_count']:,} null entries</div>
            </div>
            <div class="card-stat {imb_status}-border">
                <div class="title">Imbalance Status</div>
                <div class="value">
                    <span class="badge badge-system {imb_status}">
                        {"IMBALANCED" if stats['class_imbalance_warning'] else "BALANCED"}
                    </span>
                </div>
                <div class="subtitle">Target: label</div>
            </div>
        </div>

        <div class="section-title">
            <span>General Statistics & Data Quality</span>
        </div>

        <div class="layout-split">
            
            <div class="card-box">
                <h3>Class Distribution Imbalance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Traffic Label</th>
                            <th>Frequency Count</th>
                            <th>Relative Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        {class_rows_html}
                    </tbody>
                </table>
                
                <div class="img-container">
                    <img src="data:image/png;base64,{b64_class}" alt="Class Distribution Bar Chart">
                </div>
            </div>

            <div class="card-box">
                <h3>Missing values / Quality Metrics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Column/Dimension Name</th>
                            <th>Missing Entries</th>
                            <th>Percent Nulls</th>
                        </tr>
                    </thead>
                    <tbody>
                        {missing_rows_html}
                    </tbody>
                </table>
                
                <h3 style="margin-top: 30px;">Data Type Distribution</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Variable Data Type</th>
                            <th>Column Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td><code>{k}</code></td><td>{v}</td></tr>" for k, v in stats['dtypes'].items())}
                    </tbody>
                </table>
            </div>

        </div>

        <div class="section-title">
            <span>Feature Correlation Analysis</span>
        </div>

        <div class="layout-split">
            <div class="card-box">
                <h3>High Correlation Multicollinearity Pairs (&gt; 0.90)</h3>
                <p class="text-muted" style="font-size:12px; margin-bottom:15px;">
                    Highly correlated features often contain redundant information. Standard modeling techniques benefit from dropping one of the variables in these pairs.
                </p>
                <table>
                    <thead>
                        <tr>
                            <th>Feature 1</th>
                            <th>Feature 2</th>
                            <th class="text-center">Corr Coefficient</th>
                        </tr>
                    </thead>
                    <tbody>
                        {corr_rows_html}
                    </tbody>
                </table>
            </div>

            <div class="card-box">
                <h3>Top Correlation Matrix Heatmap</h3>
                <div class="img-container">
                    <img src="data:image/png;base64,{b64_corr}" alt="Correlation Heatmap">
                </div>
            </div>
        </div>

        <div class="section-title">
            <span>Outlier & Feature Distributions</span>
        </div>

        <div class="card-box">
            <h3>Outlier Statistics (Interquartile Range Method)</h3>
            <p class="text-muted" style="font-size:12px; margin-bottom:15px;">
                Outliers are detected as values falling below <code>Q1 - 1.5 * IQR</code> or above <code>Q3 + 1.5 * IQR</code>. Large outlier percentages are common in network telemetry bursts.
            </p>
            <div class="layout-split">
                <div>
                    <table>
                        <thead>
                            <tr>
                                <th>Feature Name</th>
                                <th>Outliers Detected</th>
                                <th>Outlier Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {outlier_rows_html}
                        </tbody>
                    </table>
                </div>
                <div>
                    <div class="img-container" style="margin-top:-10px;">
                        <img src="data:image/png;base64,{b64_box}" alt="Outlier Boxplots Grid">
                    </div>
                </div>
            </div>
        </div>

        <div class="card-box">
            <h3>Histograms and Density Graphs</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{b64_hist}" alt="Histograms Density Graphs Grid">
            </div>
        </div>

        <div class="card-box">
            <h3>KDE Distributives split by Label (Benign vs Malicious)</h3>
            <div class="img-container">
                <img src="data:image/png;base64,{b64_split}" alt="KDE Split Distribution Grid">
            </div>
        </div>

        <div class="section-title">
            <span>Numerical Feature Statistics Details</span>
        </div>

        <div class="card-box" style="overflow-x: auto;">
            <h3>Numerical Features Summary (Top 15 sorted by variance)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Median</th>
                        <th>Max</th>
                        <th>Outliers</th>
                    </tr>
                </thead>
                <tbody>
                    {stats_rows_html}
                </tbody>
            </table>
        </div>

    </div>

    <footer>
        <p>&copy; 2026 NIDS. All Rights Reserved. Model-Ready Architecture skeleton.</p>
    </footer>

</body>
</html>
"""
        return html
