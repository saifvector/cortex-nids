"""
Unit tests for Model Registry, Model Factory, Model Trainer, and Training Pipeline components.
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from src.model_registry import MODEL_REGISTRY, get_supported_models
from src.model_factory import ModelFactory
from src.model_trainer import ModelTrainer
from src.train import compute_class_weights, train_and_evaluate_all, select_best_model, compile_metadata
from src.exceptions.custom_exceptions import ConfigurationError


class DummySettings:
    """Mock configurations settings class for training testing."""
    
    class ProjectSettings:
        random_state = 42
    
    class PathSettings:
        models_dir = "models"
        
    class ModelParamsSettings:
        logistic_regression = {"max_iter": 10}
        decision_tree = {"max_depth": 3}
        random_forest = {"n_estimators": 2, "max_depth": 3, "n_jobs": 1}
        extra_trees = {"n_estimators": 2, "max_depth": 3, "n_jobs": 1}
        xgboost = {"n_estimators": 2, "max_depth": 3, "n_jobs": 1}
        lightgbm = {"n_estimators": 2, "max_depth": 3, "n_jobs": 1}
        catboost = {"iterations": 2, "depth": 3, "thread_count": 1, "verbose": 0}

    def __init__(self):
        self.project = self.ProjectSettings()
        self.paths = self.PathSettings()
        self.model = self.ModelParamsSettings()


@pytest.fixture
def dummy_train_splits():
    """Generates a small synthetic multiclass dataset for training tests."""
    np.random.seed(42)
    n_train = 100
    n_test = 20
    n_features = 4
    
    X_train = pd.DataFrame(
        np.random.normal(0, 1, (n_train, n_features)),
        columns=[f"feat_{i}" for i in range(n_features)]
    )
    y_train = pd.Series(np.random.choice([0, 1, 2], n_train, p=[0.7, 0.2, 0.1]))
    
    X_test = pd.DataFrame(
        np.random.normal(0, 1, (n_test, n_features)),
        columns=[f"feat_{i}" for i in range(n_features)]
    )
    y_test = pd.Series(np.random.choice([0, 1, 2], n_test, p=[0.7, 0.2, 0.1]))
    
    return X_train, X_test, y_train, y_test


def test_model_registry():
    """Verify registry contains all 7 required model mappings."""
    supported = get_supported_models()
    assert "logistic_regression" in supported
    assert "decision_tree" in supported
    assert "random_forest" in supported
    assert "extra_trees" in supported
    assert "xgboost" in supported
    assert "lightgbm" in supported
    assert "catboost" in supported
    assert len(supported) == 7


def test_model_factory_creation():
    """Verify that ModelFactory instantiates scikit-learn, xgboost, lightgbm, and catboost correctly."""
    factory = ModelFactory()
    random_state = 42
    class_weights = {0: 1.0, 1: 5.0, 2: 10.0}

    # Test Scikit-learn
    rf = factory.create_model("random_forest", {"n_estimators": 5}, random_state, class_weights)
    assert rf.n_estimators == 5
    assert rf.class_weight == class_weights
    assert rf.random_state == random_state

    # Test LightGBM
    lgb = factory.create_model("lightgbm", {"n_estimators": 5}, random_state, class_weights)
    assert lgb.n_estimators == 5
    assert lgb.class_weight == class_weights

    # Test CatBoost
    cat = factory.create_model("catboost", {"iterations": 5}, random_state, class_weights)
    assert cat.get_params()["iterations"] == 5
    assert cat.get_params()["class_weights"] == class_weights

    # Test XGBoost
    xgb = factory.create_model("xgboost", {"n_estimators": 5}, random_state, class_weights)
    assert xgb.n_estimators == 5
    assert not hasattr(xgb, "class_weight") # XGBoost does not have class_weight constructor param for multiclass

    # Invalid algorithm name
    with pytest.raises(ConfigurationError):
        factory.create_model("unsupported_classifier", {}, random_state)


def test_model_trainer_profiling(dummy_train_splits):
    """Verify that ModelTrainer fits, measures latency and computes multiclass metrics."""
    X_train, X_test, y_train, y_test = dummy_train_splits
    factory = ModelFactory()
    trainer = ModelTrainer()
    
    dt_instance = factory.create_model("decision_tree", {"max_depth": 3}, 42)
    fitted_model, stats = trainer.train_and_profile(
        model_name="decision_tree",
        model_instance=dt_instance,
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test
    )
    
    assert stats["Accuracy"] >= 0.0
    assert stats["Precision"] >= 0.0
    assert stats["Recall"] >= 0.0
    assert stats["F1 Score"] >= 0.0
    assert stats["ROC AUC"] >= 0.0
    assert stats["False Positive Rate"] >= 0.0
    assert stats["Training Time"] > 0.0
    assert stats["Prediction Time"] > 0.0
    assert stats["Memory Usage"] >= 0.0


def test_train_pipeline_orchestration(dummy_train_splits, tmp_path):
    """Verify the orchestration pipeline trains all models, rankings, best model, and metadata."""
    X_train, X_test, y_train, y_test = dummy_train_splits
    
    settings = DummySettings()
    # Override settings models_dir to test folder path
    settings.paths.models_dir = tmp_path
    
    comparison_df, trained_models, feature_importances = train_and_evaluate_all(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        settings=settings
    )
    
    # 7 models trained
    assert len(trained_models) == 7
    assert comparison_df.shape[0] == 7
    assert "Model" in comparison_df.columns
    
    # Check that model joblib files exist
    for model_name in trained_models.keys():
        assert (tmp_path / f"{model_name}.joblib").exists()

    # Verify best model selection
    best_model_name, best_model_instance = select_best_model(comparison_df, trained_models, settings)
    assert best_model_name in trained_models
    assert (tmp_path / "best_model.joblib").exists()
    
    # Verify metadata compilation
    meta = compile_metadata(best_model_name, X_train.shape, X_train.shape[1], 12.34)
    assert meta["model_name"] == best_model_name
    assert meta["feature_count"] == X_train.shape[1]
    assert "scikit-learn" in meta["dependency_versions"]
