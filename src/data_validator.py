"""
DataValidator module for NIDS.
Performs checks on raw and merged datasets for missing values, duplicates,
infinite values, wrong datatypes, constant features, empty columns, and memory footprints.
"""
import logging
from typing import Any, Dict, List
import numpy as np
import pandas as pd


class DataValidator:
    """
    OOP Data Validator class. Computes extensive statistics on data quality
    and returns a structured validation report.
    """

    def __init__(self, target_column: str = "Label"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column

    def run_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes all validation tests and packages results into a dict.
        """
        self.logger.info("Starting automated dataset validation checks...")
        num_rows, num_cols = df.shape

        if num_rows == 0:
            return {"error": "Dataset is empty."}

        report = {}

        # 1. Base Dimensions & Column Types
        report["dimensions"] = {"rows": num_rows, "cols": num_cols}
        
        dtypes_dict = {}
        for col in df.columns:
            dtypes_dict[col] = str(df[col].dtype)
        report["dtypes"] = dtypes_dict

        # 2. Memory Usage (overall and by column in MBs)
        self.logger.debug("Calculating memory footprints...")
        col_memory = df.memory_usage(deep=True) / (1024 * 1024)  # convert to MB
        report["memory_usage"] = {
            "total_mb": float(col_memory.sum()),
            "by_column": {str(k): float(v) for k, v in col_memory.items()}
        }

        # 3. Missing Values & Empty Columns
        self.logger.debug("Checking missing values...")
        null_counts = df.isnull().sum()
        total_nulls = int(null_counts.sum())
        null_percentages = (null_counts / num_rows * 100).to_dict()
        
        empty_columns = null_counts[null_counts == num_rows].index.tolist()

        report["missing_values"] = {
            "total_count": total_nulls,
            "overall_null_percentage": (total_nulls / (num_rows * num_cols) * 100) if num_cols > 0 else 0.0,
            "by_column_count": {str(k): int(v) for k, v in null_counts.items() if v > 0},
            "by_column_percentage": {str(k): float(v) for k, v in null_percentages.items() if v > 0},
            "empty_columns": empty_columns
        }

        # 4. Duplicate Rows
        self.logger.debug("Checking duplicate rows...")
        dup_rows = int(df.duplicated().sum())
        report["duplicate_rows"] = {
            "count": dup_rows,
            "percentage": (dup_rows / num_rows * 100)
        }

        # 5. Duplicate Columns (Identical by name or identical by values)
        self.logger.debug("Checking duplicate columns...")
        # Name duplicates (should be stripped, but check if there are columns with exact same name)
        col_names = list(df.columns)
        dup_col_names = list(set([x for x in col_names if col_names.count(x) > 1]))
        
        # Value duplicates (columns that contain the exact same data)
        # Note: checking all pairs can be slow on 80+ features, so we do it efficiently.
        dup_col_content = []
        # Sample 5000 rows to speed up duplicate check if dataset is very large
        sample_size = min(5000, num_rows)
        sample_df = df.sample(n=sample_size, random_state=42) if num_rows > sample_size else df
        
        numeric_sample = sample_df.select_dtypes(include=[np.number])
        if not numeric_sample.empty and numeric_sample.shape[1] > 1:
            checked = set()
            for col_a in numeric_sample.columns:
                if col_a in checked:
                    continue
                for col_b in numeric_sample.columns:
                    if col_a == col_b or col_b in checked:
                        continue
                    # Quick check on sample first
                    if (numeric_sample[col_a] == numeric_sample[col_b]).all():
                        # Validate on full dataframe if samples match
                        if (df[col_a] == df[col_b]).all():
                            dup_col_content.append((col_a, col_b))
                            checked.add(col_b)

        report["duplicate_columns"] = {
            "by_name": dup_col_names,
            "by_content": [[a, b] for a, b in dup_col_content]
        }

        # 6. Infinite Values
        self.logger.debug("Checking infinite values...")
        inf_columns_count = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            infs = int(np.isinf(df[col]).sum())
            if infs > 0:
                inf_columns_count[col] = infs
                
        report["infinite_values"] = {
            "total_count": sum(inf_columns_count.values()),
            "by_column": inf_columns_count
        }

        # 7. Wrong Datatypes & Invalid Numeric Values
        # Look for non-numeric/string values inside columns that should be numeric
        self.logger.debug("Auditing non-numeric values in numeric columns...")
        invalid_numeric_counts = {}
        object_cols = df.select_dtypes(include=["object"]).columns
        object_cols = [c for c in object_cols if c != self.target_column]

        for col in object_cols:
            # Check if it could be numeric
            converted = pd.to_numeric(df[col], errors="coerce")
            nan_diff = converted.isnull().sum() - df[col].isnull().sum()
            if nan_diff > 0 and (converted.notnull().sum() > 0):
                # This means it's a mixed type column (mainly numbers but has some strings)
                invalid_numeric_counts[col] = int(nan_diff)

        report["invalid_numeric_values"] = {
            "by_column": invalid_numeric_counts
        }

        # 8. Constant Features (0 variance or 1 unique value)
        self.logger.debug("Detecting constant features...")
        constant_features = []
        for col in df.columns:
            if df[col].nunique() <= 1:
                constant_features.append(col)
        
        # Check low variance for numerical features
        low_variance_features = []
        for col in numeric_cols:
            if col not in constant_features:
                var = df[col].var()
                if pd.isnull(var) or var < 1e-6:
                    low_variance_features.append(col)

        report["constant_features"] = {
            "count": len(constant_features),
            "columns": constant_features,
            "low_variance_columns": low_variance_features
        }

        self.logger.info("Dataset validation checks completed.")
        return report
