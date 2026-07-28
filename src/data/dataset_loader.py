"""
Dataset Loader module for the Network Intrusion Detection System (NIDS).
Handles scanning, loading, schema validation, and cleaning of raw CSV telemetry datasets.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Union
import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import DataPreprocessingError, ConfigurationError
from src.utils.utils import get_absolute_path


class DatasetLoader:
    """
    OOP Loader class for raw network telemetry datasets (e.g., CICIDS2017).
    """

    def __init__(self, target_column: str = "label", drop_columns: List[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column
        self.drop_columns = drop_columns or []

    def find_csv_files(self, data_path: Union[str, Path]) -> List[Path]:
        """
        Scans data_path for CSV files.
        If data_path is a directory, searches recursively. If it's a file, returns it in a list.
        """
        path = get_absolute_path(data_path)
        if path.is_file():
            if path.suffix.lower() == ".csv":
                return [path]
            raise ConfigurationError(f"Provided path is not a CSV file: {path}")
        
        if path.is_dir():
            csv_files = list(path.glob("**/*.csv"))
            if not csv_files:
                raise ConfigurationError(f"No CSV files found in directory: {path}")
            return csv_files
            
        raise ConfigurationError(f"Data path does not exist: {path}")

    def load_raw_data(self, data_path: Union[str, Path]) -> pd.DataFrame:
        """
        Loads and concatenates raw CSV files from the specified data_path.
        """
        csv_files = self.find_csv_files(data_path)
        self.logger.info("Found %d CSV file(s) to load.", len(csv_files))

        loaded_dfs = []
        for csv_file in csv_files:
            self.logger.info("Loading dataset file: %s", csv_file.name)
            try:
                # Read CSV file (using low_memory=False to avoid type warnings)
                df = pd.read_csv(csv_file, low_memory=False)
                loaded_dfs.append(df)
                self.logger.debug("Successfully loaded %s with shape %s", csv_file.name, df.shape)
            except Exception as e:
                raise DataPreprocessingError(f"Failed to read CSV file {csv_file}: {e}") from e

        if not loaded_dfs:
            raise DataPreprocessingError("No data could be loaded.")

        # Concatenate all datasets if there are multiple CSV files
        try:
            combined_df = pd.concat(loaded_dfs, ignore_index=True)
            self.logger.info("Concatenated dataset shape: %s", combined_df.shape)
            return combined_df
        except Exception as e:
            raise DataPreprocessingError(f"Failed to concatenate loaded datasets: {e}") from e

    def clean_data(self, df: pd.DataFrame, drop_duplicates: bool = True, impute_strategy: str = "median") -> pd.DataFrame:
        """
        Cleans the loaded dataframe:
        1. Strips leading/trailing whitespaces from column names.
        2. Replaces infinite values (np.inf, -np.inf) with np.nan.
        3. Identifies and handles missing values (imputes using specified strategy).
        4. Drops duplicate rows if drop_duplicates is True.
        5. Converts object/string columns to numeric (except target_column).
        """
        self.logger.info("Beginning dataset cleaning phase...")
        cleaned_df = df.copy()

        # 1. Clean column names
        cleaned_df.columns = [col.strip() for col in cleaned_df.columns]
        self.logger.debug("Cleaned whitespaces from column names.")

        # Validate that the target column exists
        cleaned_target = self.target_column.strip()
        if cleaned_target not in cleaned_df.columns:
            # Fallback check in case the labels are named differently (e.g., 'Label')
            alt_targets = [col for col in cleaned_df.columns if col.lower() == cleaned_target.lower()]
            if alt_targets:
                cleaned_target = alt_targets[0]
                self.target_column = cleaned_target
                self.logger.info("Target column resolved to: %s", cleaned_target)
            else:
                raise DataPreprocessingError(f"Target column '{self.target_column}' not found in dataset columns: {list(cleaned_df.columns)}")

        # 2. Handle infinite values
        # Network telemetry often has inf values in speed/duration ratios when time is 0
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
        # Also find object cols that might contain string representations of infinity or numeric data
        object_cols = cleaned_df.select_dtypes(exclude=[np.number]).columns
        object_cols = [col for col in object_cols if col != cleaned_target]

        # For object cols, attempt to force convert to float (except label column)
        for col in object_cols:
            try:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
                self.logger.debug("Forced column '%s' to numeric.", col)
            except Exception as e:
                self.logger.warning("Could not convert column '%s' to numeric: %s", col, e)

        # Refresh numeric columns list after forcing conversions
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns

        inf_mask = np.isinf(cleaned_df[numeric_cols])
        inf_count = inf_mask.sum().sum()
        if inf_count > 0:
            self.logger.info("Detected %d infinite value(s). Replacing with NaN.", inf_count)
            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].replace([np.inf, -np.inf], np.nan)

        # 3. Handle missing values (NaN)
        missing_count = cleaned_df.isnull().sum().sum()
        if missing_count > 0:
            self.logger.info("Detected %d missing value(s). Imputing using strategy: %s.", missing_count, impute_strategy)
            for col in numeric_cols:
                col_missing = cleaned_df[col].isnull().sum()
                if col_missing > 0:
                    if impute_strategy == "mean":
                        fill_val = cleaned_df[col].mean()
                    elif impute_strategy == "median":
                        fill_val = cleaned_df[col].median()
                    elif impute_strategy == "zero":
                        fill_val = 0.0
                    else:
                        raise ConfigurationError(f"Unsupported imputation strategy: {impute_strategy}")
                    
                    # If whole column is NaN, fill with 0
                    if pd.isnull(fill_val):
                        fill_val = 0.0
                        
                    cleaned_df[col] = cleaned_df[col].fillna(fill_val)
                    self.logger.debug("Imputed column '%s' missing %d values with %s", col, col_missing, fill_val)

        # 4. Handle duplicates
        if drop_duplicates:
            dup_count = cleaned_df.duplicated().sum()
            if dup_count > 0:
                self.logger.info("Detected %d duplicate row(s). Removing duplicates.", dup_count)
                cleaned_df = cleaned_df.drop_duplicates(ignore_index=True)

        # 5. Drop unnecessary columns
        cols_to_drop_present = [col for col in self.drop_columns if col in cleaned_df.columns]
        if cols_to_drop_present:
            self.logger.info("Dropping columns as specified by config: %s", cols_to_drop_present)
            cleaned_df = cleaned_df.drop(columns=cols_to_drop_present)

        self.logger.info("Cleaning completed. Final dataset shape: %s", cleaned_df.shape)
        return cleaned_df

    def split_features_and_labels(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Splits the dataframe into a feature matrix X and a target series y.
        """
        if self.target_column not in df.columns:
            raise DataPreprocessingError(f"Target column '{self.target_column}' is missing from the dataset.")

        X = df.drop(columns=[self.target_column])
        y = df[self.target_column]
        return X, y
