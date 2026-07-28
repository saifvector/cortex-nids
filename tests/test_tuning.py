"""
Unit tests for Hyperparameter Tuning Search Spaces, Model Optimizer, and tuning loop coordinator.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.search_spaces import get_search_space
from src.model_optimizer import ModelOptimizer
from src.hyperparameter_tuning import tune_and_profile_all
from tests.test_training import DummySettings, dummy_train_splits


def test_search_spaces():
    """Verify that get_search_space returns correct dictionaries for classifiers."""
    rf_space = get_search_space("random_forest")
    assert "n_estimators" in rf_space
    assert "max_depth" in rf_space
    assert isinstance(rf_space["n_estimators"], list)

    xgb_space = get_search_space("xgboost")
    assert "learning_rate" in xgb_space
    assert "n_estimators" in xgb_space

    with pytest.raises(ValueError):
        get_search_space("logistic_regression")  # Skip LR search space


def test_stratified_sampling(dummy_train_splits):
    """Verify ModelOptimizer stratified sampling reduces size while maintaining class labels."""
    X_train, X_test, y_train, y_test = dummy_train_splits
    optimizer = ModelOptimizer()

    sample_size = 30
    X_samp, y_samp = optimizer.stratified_sample(X_train, y_train, sample_size, 42)

    assert len(X_samp) == sample_size
    assert len(y_samp) == sample_size
    assert set(y_samp.unique()).issubset(y_train.unique())


def test_optimizer_optimization(dummy_train_splits):
    """Verify that ModelOptimizer executes randomized searches with CV folds."""
    X_train, X_test, y_train, y_test = dummy_train_splits
    optimizer = ModelOptimizer()

    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(random_state=42)

    best_params, best_estimator = optimizer.optimize_hyperparameters(
        model_name="random_forest",
        estimator=rf,
        X_train_sample=X_train,
        y_train_sample=y_train,
        search_method="randomized",
        cv_folds=3,
        n_iter=2,
        random_state=42
    )

    assert isinstance(best_params, dict)
    assert "max_depth" in best_params
    assert best_estimator is not None
