"""
Unit tests for data splitting, category encoding, scaling, feature selection, and preprocessing pipelines.
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from src.split_data import stratified_split
from src.scaling import FeatureScaler
from src.encoding import CategoricalEncoder
from src.feature_selection import FeatureSelector
from src.preprocessing import PreprocessingPipeline


@pytest.fixture
def dummy_dataset():
    """Generates a simple dummy dataset with target labels and mixed feature types."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        "numeric_1": np.random.normal(0, 1, n_samples),
        "numeric_2": np.random.normal(5, 10, n_samples),
        "numeric_3": np.random.normal(0, 1, n_samples), # Highly correlated with numeric_1
        "constant_col": np.ones(n_samples),
        "low_var_col": np.random.normal(0, 0.00001, n_samples),
        "duplicate_col": np.zeros(n_samples), # Will be identical to constant_col after low_var changes
        "categorical_col": np.random.choice(["TypeA", "TypeB", "TypeC"], n_samples),
        "target": np.random.choice(["BENIGN", "DDoS"], n_samples, p=[0.8, 0.2])
    }
    
    # Introduce high correlation
    data["numeric_3"] = data["numeric_1"] * 0.99 + np.random.normal(0, 0.01, n_samples)
    data["duplicate_col"] = data["numeric_1"].copy()
    
    df = pd.DataFrame(data)
    return df


def test_stratified_split(dummy_dataset):
    """Verify that stratified_split splits features and labels preserving class ratios."""
    X_train, X_test, y_train, y_test = stratified_split(
        df=dummy_dataset,
        target_column="target",
        test_size=0.2,
        random_state=42,
        stratify=True
    )
    
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert "target" not in X_train.columns
    assert len(y_train) == 80
    assert len(y_test) == 20
    
    # Stratified check
    ratio_train = (y_train == "DDoS").mean()
    ratio_test = (y_test == "DDoS").mean()
    assert abs(ratio_train - ratio_test) < 0.05


def test_feature_scaler(dummy_dataset):
    """Verify standard, minmax, and robust scaling transforms."""
    numeric_df = dummy_dataset[["numeric_1", "numeric_2"]]
    
    # Standard
    scaler_std = FeatureScaler(method="standard")
    scaled_std = scaler_std.fit_transform(numeric_df)
    assert abs(scaled_std["numeric_1"].mean()) < 1e-7
    assert abs(scaled_std["numeric_1"].std(ddof=0) - 1.0) < 1e-5
    
    # MinMax
    scaler_minmax = FeatureScaler(method="minmax")
    scaled_minmax = scaler_minmax.fit_transform(numeric_df)
    assert abs(scaled_minmax["numeric_1"].min() - 0.0) < 1e-7
    assert abs(scaled_minmax["numeric_1"].max() - 1.0) < 1e-7

    # Robust
    scaler_robust = FeatureScaler(method="robust")
    scaled_robust = scaler_robust.fit_transform(numeric_df)
    assert scaled_robust.shape == numeric_df.shape


def test_categorical_encoder(dummy_dataset):
    """Verify label encoding and OHE column expansion."""
    X = dummy_dataset.drop(columns=["target"])
    y = dummy_dataset["target"]
    
    encoder = CategoricalEncoder()
    X_trans = encoder.fit_transform_features(X)
    y_trans = encoder.fit_transform_target(y)
    
    # OHE test
    assert "categorical_col" not in X_trans.columns
    assert "categorical_col_TypeA" in X_trans.columns
    assert "categorical_col_TypeB" in X_trans.columns
    
    # Label Encoder test
    assert y_trans.dtype == np.int64 or y_trans.dtype == np.int32
    assert set(y_trans.unique()).issubset({0, 1})
    assert encoder.label_mapping["BENIGN"] == 0 or encoder.label_mapping["BENIGN"] == 1


def test_feature_selector(dummy_dataset):
    """Verify that FeatureSelector drops constant, low var, duplicate, and correlated columns."""
    X = dummy_dataset.drop(columns=["target"])
    
    # We must first encode categorical before doing feature selection
    encoder = CategoricalEncoder()
    X_encoded = encoder.fit_transform_features(X)
    y = pd.Series(np.random.choice([0, 1], len(X_encoded)))
    
    selector = FeatureSelector(
        variance_threshold=0.0001,
        correlation_threshold=0.90,
        top_n_mi=4,
        top_n_rfe=4,
        random_state=42
    )
    
    X_selected = selector.fit_transform(X_encoded, y)
    
    # Constant column dropped
    assert "constant_col" in selector.constant_cols
    assert "constant_col" not in X_selected.columns
    
    # Low variance column dropped
    assert "low_var_col" in selector.low_variance_cols
    assert "low_var_col" not in X_selected.columns
    
    # Duplicate column dropped
    assert "duplicate_col" in selector.duplicate_cols
    assert "duplicate_col" not in X_selected.columns
    
    # Highly correlated dropped
    assert "numeric_3" in selector.highly_correlated_cols
    assert "numeric_3" not in X_selected.columns
    
    # MI rankings and RFE rankings should exist
    assert len(selector.mi_scores) > 0
    assert len(selector.rfe_rankings) > 0
    assert len(selector.selected_features) == 4


def test_preprocessing_pipeline(dummy_dataset, tmp_path):
    """Verify PreprocessingPipeline integration, resampling support, and joblib save/load."""
    X = dummy_dataset.drop(columns=["target"])
    y = dummy_dataset["target"]
    
    pipeline = PreprocessingPipeline(config={
        "scaling_method": "standard",
        "variance_threshold": 0.0001,
        "correlation_threshold": 0.90,
        "top_n_mi": 4,
        "top_n_rfe": 4,
        "balancing_method": "smote",
        "random_state": 42
    })
    
    X_train_trans, y_train_trans = pipeline.fit_transform(X, y)
    
    # Check transformed train set shapes
    assert X_train_trans.shape[1] == 4
    assert y_train_trans.shape[0] == len(dummy_dataset)
    
    # Check resampling
    X_res, y_res, balance_stats = pipeline.apply_resampling(X_train_trans, y_train_trans)
    # Target class distribution should now be perfectly balanced (50/50)
    assert y_res.value_counts().min() == y_res.value_counts().max()
    assert balance_stats["resampled"] is True

    # Test serialization
    pipeline_file = tmp_path / "pipeline.joblib"
    pipeline.save(pipeline_file)
    assert pipeline_file.exists()
    
    # Load pipeline
    loaded_pipeline = PreprocessingPipeline.load(pipeline_file)
    assert loaded_pipeline.is_fitted is True
    assert loaded_pipeline.scaling_method == "standard"
    assert len(loaded_pipeline.final_features) == 4
    
    # Transform test features
    X_test_trans = loaded_pipeline.transform(X)
    assert X_test_trans.shape == X_train_trans.shape
