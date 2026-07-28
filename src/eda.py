"""
EDAAnalyzer module for NIDS.
Profiles dataset statistical summaries, target class frequencies,
outliers using the IQR method, variance metrics, Pearson/Spearman correlations,
and identifies duplicate columns.
"""
import logging
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import NIDSException


class EDAAnalyzer:
    """
    OOP Exploratory Data Analysis profiler.
    Computes statistical characteristics, class imbalance index, outliers,
    and correlations.
    """

    def __init__(self, target_column: str = "Label"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column

    def analyze(self, df: pd.DataFrame, correlation_threshold: float = 0.90) -> Dict[str, Any]:
        """
        Runs the complete EDA profiling pipeline.
        """
        self.logger.info("Executing comprehensive Exploratory Data Analysis...")
        results = {}

        num_rows, num_cols = df.shape
        results["shape"] = {"rows": num_rows, "cols": num_cols}
        results["columns"] = list(df.columns)
        results["dtypes"] = {str(k): str(v) for k, v in df.dtypes.items()}

        # 1. Target Label Distribution & Imbalance
        if self.target_column in df.columns:
            counts = df[self.target_column].value_counts()
            pcts = df[self.target_column].value_counts(normalize=True) * 100
            
            target_dist = []
            for label, count in counts.items():
                target_dist.append({
                    "class": str(label),
                    "count": int(count),
                    "percentage": float(pcts[label])
                })
            results["target_distribution"] = target_dist
            
            # Class imbalance check
            min_pct = pcts.min()
            results["class_imbalance_warning"] = bool(min_pct < 5.0)
            results["min_class_percentage"] = float(min_pct)
        else:
            results["target_distribution"] = []
            results["class_imbalance_warning"] = False
            results["min_class_percentage"] = 0.0

        # 2. Outlier Analysis (using IQR method)
        self.logger.debug("Running IQR outlier checks on numerical features...")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c != self.target_column]

        outliers_dict = {}
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            col_outliers = int(((df[col] < lower_bound) | (df[col] > upper_bound)).sum())
            outliers_dict[col] = {
                "count": col_outliers,
                "percentage": (col_outliers / num_rows * 100) if num_rows > 0 else 0.0,
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr)
            }
        results["outliers"] = outliers_dict

        # 3. Feature Variance & Detailed Statistics
        self.logger.debug("Computing variance and detailed feature statistics...")
        stats_list = []
        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            min_val = df[col].min()
            median_val = df[col].median()
            max_val = df[col].max()
            var_val = df[col].var()
            q25 = df[col].quantile(0.25)
            q75 = df[col].quantile(0.75)

            stats_list.append({
                "feature": col,
                "mean": float(mean_val) if not pd.isnull(mean_val) else 0.0,
                "std": float(std_val) if not pd.isnull(std_val) else 0.0,
                "min": float(min_val) if not pd.isnull(min_val) else 0.0,
                "25%": float(q25) if not pd.isnull(q25) else 0.0,
                "50%": float(median_val) if not pd.isnull(median_val) else 0.0,
                "75%": float(q75) if not pd.isnull(q75) else 0.0,
                "max": float(max_val) if not pd.isnull(max_val) else 0.0,
                "variance": float(var_val) if not pd.isnull(var_val) else 0.0
            })
        
        # Sort features by variance descending
        results["feature_statistics"] = sorted(stats_list, key=lambda x: x["variance"], reverse=True)

        # 4. Pearson & Spearman Correlations
        # Because Spearman is rank-based and extremely expensive for large datasets (e.g. 2.8M rows),
        # we compute Spearman on a representative sample (max 50,000 rows).
        # We also sample Pearson if the dataset is massive, to ensure quick UI response.
        sample_size = 50000
        if num_rows > sample_size:
            self.logger.info("Dataset shape %s exceeds limit. Sampling %d rows for correlation calculations...", df.shape, sample_size)
            sample_df = df.sample(n=sample_size, random_state=42)
        else:
            sample_df = df

        num_sample_df = sample_df.select_dtypes(include=[np.number])
        if self.target_column in num_sample_df.columns:
            num_sample_df = num_sample_df.drop(columns=[self.target_column])

        # Pearson correlation matrix
        self.logger.debug("Calculating Pearson correlation...")
        pearson_corr = num_sample_df.corr(method="pearson")
        
        # Spearman correlation matrix
        self.logger.debug("Calculating Spearman correlation...")
        spearman_corr = num_sample_df.corr(method="spearman")

        results["correlations"] = {
            "pearson_matrix": pearson_corr,
            "spearman_matrix": spearman_corr
        }

        # 5. Identify highly correlated features
        results["high_correlations_pearson"] = self._find_high_correlations(pearson_corr, correlation_threshold)
        results["high_correlations_spearman"] = self._find_high_correlations(spearman_corr, correlation_threshold)

        # 6. Duplicate Feature Detection (identical values)
        self.logger.debug("Checking identical value duplicate features...")
        dup_features = []
        if not num_sample_df.empty and num_sample_df.shape[1] > 1:
            checked = set()
            for col_a in num_sample_df.columns:
                if col_a in checked:
                    continue
                for col_b in num_sample_df.columns:
                    if col_a == col_b or col_b in checked:
                        continue
                    # Check sample first
                    if (num_sample_df[col_a] == num_sample_df[col_b]).all():
                        # Verify on full dataframe
                        if (df[col_a] == df[col_b]).all():
                            dup_features.append((col_a, col_b))
                            checked.add(col_b)

        results["duplicate_features"] = dup_features

        self.logger.info("Exploratory Data Analysis profile generated successfully.")
        return results

    def _find_high_correlations(self, corr_matrix: pd.DataFrame, threshold: float) -> List[Dict[str, Any]]:
        """Helper to extract feature pairs with correlation above threshold."""
        high_corr = []
        upper_tri = corr_matrix.abs().where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        
        for col_name in upper_tri.columns:
            matches = upper_tri[col_name][upper_tri[col_name] > threshold]
            for row_name, coeff in matches.items():
                high_corr.append({
                    "feature_1": str(row_name),
                    "feature_2": str(col_name),
                    "coefficient": float(corr_matrix.at[row_name, col_name])
                })
        # Sort descending by absolute coefficient
        return sorted(high_corr, key=lambda x: abs(x["coefficient"]), reverse=True)
