"""
DataLoader module for NIDS.
Automatically scans data/raw for CSV files, validates column consistency,
merges datasets, cleans duplicates and infinites, and saves the result to data/processed.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Union
import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import DataPreprocessingError, ConfigurationError
from src.utils.utils import get_absolute_path, ensure_directory


class DataLoader:
    """
    OOP Data Loader and Preprocessor for raw NIDS CSV files.
    """

    def __init__(self, target_column: str = "Label"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = target_column

    def scan_raw_directory(self, raw_dir: Union[str, Path]) -> List[Path]:
        """
        Scans raw_dir and lists all CSV files.
        """
        dir_path = get_absolute_path(raw_dir)
        if not dir_path.exists() or not dir_path.is_dir():
            raise ConfigurationError(f"Raw data directory does not exist: {dir_path}")

        csv_files = list(dir_path.glob("*.csv"))
        if not csv_files:
            raise DataPreprocessingError(f"No CSV files found in {dir_path}")
        
        self.logger.info("Found %d raw CSV files in %s.", len(csv_files), dir_path)
        return csv_files

    def load_and_merge(self, csv_files: List[Path]) -> pd.DataFrame:
        """
        Loads all CSV files and merges them after validating column alignment.
        """
        if not csv_files:
            raise DataPreprocessingError("List of CSV files is empty.")

        loaded_dfs = []
        base_columns = None
        base_file = None

        for file_path in csv_files:
            self.logger.info("Reading file: %s", file_path.name)
            try:
                # Read only header first to validate schema quickly
                df_header = pd.read_csv(file_path, nrows=0)
                # Clean column headers
                cleaned_columns = [col.strip() for col in df_header.columns]
                
                if base_columns is None:
                    base_columns = cleaned_columns
                    base_file = file_path.name
                else:
                    if len(cleaned_columns) != len(base_columns):
                        raise DataPreprocessingError(
                            f"Column count mismatch. File '{file_path.name}' has {len(cleaned_columns)} columns, "
                            f"but '{base_file}' has {len(base_columns)} columns."
                        )
                    # Verify column name match (unordered or ordered, let's check exact match)
                    mismatched_cols = set(cleaned_columns) ^ set(base_columns)
                    if mismatched_cols:
                        raise DataPreprocessingError(
                            f"Column schema mismatch between '{file_path.name}' and '{base_file}'. "
                            f"Mismatched columns: {mismatched_cols}"
                        )
                
                # Load the full file
                df = pd.read_csv(file_path, low_memory=False)
                # Apply column stripping
                df.columns = [col.strip() for col in df.columns]
                loaded_dfs.append(df)
                self.logger.info("Successfully loaded '%s' with shape %s", file_path.name, df.shape)

            except DataPreprocessingError as dpe:
                raise dpe
            except Exception as e:
                raise DataPreprocessingError(f"Failed to read CSV file '{file_path}': {e}") from e

        # Merge files
        try:
            merged_df = pd.concat(loaded_dfs, ignore_index=True)
            self.logger.info("Successfully merged %d files. Combined shape: %s", len(csv_files), merged_df.shape)
            return merged_df
        except Exception as e:
            raise DataPreprocessingError(f"Failed to merge loaded dataframes: {e}") from e

    def clean_obvious_issues(self, df: pd.DataFrame, impute_strategy: str = "median") -> pd.DataFrame:
        """
        Cleans obvious issues:
        1. Strips whitespaces from string labels.
        2. Removes duplicate rows (except useful attack records, we drop duplicates but keep single occurrences).
        3. Replaces positive and negative infinite values with NaN.
        4. Safely handles missing values (imputes using median to preserve rows with attack labels).
        """
        self.logger.info("Starting cleaning of obvious dataset issues...")
        cleaned_df = df.copy()

        # Resolve target column case-insensitively
        target_candidates = [col for col in cleaned_df.columns if col.lower() == self.target_column.lower()]
        if target_candidates:
            self.target_column = target_candidates[0]
            self.logger.info("Target column resolved to: %s", self.target_column)

        # Handle target column labels whitespace
        if self.target_column in cleaned_df.columns:
            # Strip trailing/leading spaces from labels
            cleaned_df[self.target_column] = cleaned_df[self.target_column].astype(str).str.strip()
            self.logger.debug("Cleaned and stripped labels in column '%s'", self.target_column)

        # 1. Replace infinities with NaN in numeric columns
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
        
        # Check other object columns for string reps of infinity and convert to numeric
        for col in cleaned_df.columns:
            if col != self.target_column and cleaned_df[col].dtype == "object":
                try:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
                    self.logger.debug("Forced column '%s' to numeric data type", col)
                except Exception:
                    pass

        # Re-fetch numeric columns list
        numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns

        inf_mask = np.isinf(cleaned_df[numeric_cols])
        total_infs = int(inf_mask.sum().sum())
        if total_infs > 0:
            self.logger.info("Replacing %d infinite value(s) with NaN.", total_infs)
            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].replace([np.inf, -np.inf], np.nan)

        # 2. Impute missing values safely
        # To avoid removing useful attack records, we do NOT drop rows containing NaN.
        # Instead, we impute numeric missing values with their median/mean.
        total_nans = int(cleaned_df.isnull().sum().sum())
        if total_nans > 0:
            self.logger.info("Found %d missing value(s). Imputing to preserve attack records...", total_nans)
            for col in numeric_cols:
                col_nans = cleaned_df[col].isnull().sum()
                if col_nans > 0:
                    if impute_strategy == "median":
                        fill_value = cleaned_df[col].median()
                    elif impute_strategy == "mean":
                        fill_value = cleaned_df[col].mean()
                    else:
                        fill_value = 0.0

                    if pd.isnull(fill_value):
                        fill_value = 0.0

                    cleaned_df[col] = cleaned_df[col].fillna(fill_value)
                    self.logger.debug("Imputed column '%s' with %s for %d NaN entries", col, fill_value, col_nans)

        # 3. Remove duplicate rows
        # Drop duplicates but reset index. Keep first occurrence (retains representative entries).
        dup_count = int(cleaned_df.duplicated().sum())
        if dup_count > 0:
            self.logger.info("Removing %d duplicate rows.", dup_count)
            # Make sure we don't accidentally wipe out distinct attack records (duplicated checks all columns,
            # so rows are only removed if they are identical in every single feature).
            cleaned_df = cleaned_df.drop_duplicates(ignore_index=True)
            
        self.logger.info("Obvious cleaning complete. Cleaned shape: %s", cleaned_df.shape)
        return cleaned_df

    def save_processed_data(self, df: pd.DataFrame, dest_path: Union[str, Path]) -> Path:
        """
        Saves the cleaned dataframe as a CSV file to the processed directory.
        """
        output_file = get_absolute_path(dest_path)
        ensure_directory(output_file.parent)
        
        self.logger.info("Saving cleaned merged dataset to: %s", output_file)
        try:
            df.to_csv(output_file, index=False)
            self.logger.info("Cleaned dataset saved successfully.")
            return output_file
        except Exception as e:
            raise DataPreprocessingError(f"Failed to write cleaned dataset to {output_file}: {e}") from e
