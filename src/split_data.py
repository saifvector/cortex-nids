"""
Split Data module for NIDS.
Handles train/test splitting with stratification on the target label column.
"""
import logging
from typing import Tuple, Union
import pandas as pd
from sklearn.model_selection import train_test_split

from src.exceptions.custom_exceptions import DataPreprocessingError


def stratified_split(
    df: pd.DataFrame,
    target_column: str,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Performs train/test split on the dataset.
    Uses stratification on the target_column to ensure class proportions are preserved.
    """
    logger = logging.getLogger("NIDS.split_data")
    logger.info("Splitting dataset: test_size=%s, stratify=%s, random_state=%d", test_size, stratify, random_state)

    if target_column not in df.columns:
        raise DataPreprocessingError(f"Target column '{target_column}' is missing from the DataFrame.")

    X = df.drop(columns=[target_column])
    y = df[target_column]

    try:
        # Stratify by y if enabled and has multiple classes with sufficient samples
        stratify_by = y if (stratify and y.nunique() > 1) else None
        
        # Verify min class samples to support stratification
        if stratify_by is not None:
            min_class_count = y.value_counts().min()
            if min_class_count < 2:
                logger.warning("Minority class has less than 2 samples. Disabling stratification for train/test split.")
                stratify_by = None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_by
        )
        
        logger.info("Split completed. Train shape: X=%s, y=%s. Test shape: X=%s, y=%s", 
                    X_train.shape, y_train.shape, X_test.shape, y_test.shape)
        return X_train, X_test, y_train, y_test

    except Exception as e:
        raise DataPreprocessingError(f"Failed to split dataset: {e}") from e
