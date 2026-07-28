"""
Model Optimizer module for NIDS.
Performs RandomizedSearchCV and GridSearchCV over parameter grids,
handles stratified training splits sampling, and manages early stopping for gradient boosters.
"""
import logging
import time
from typing import Any, Dict, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold, train_test_split
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

from src.search_spaces import get_search_space
from src.exceptions.custom_exceptions import ModelTrainingError


class ModelOptimizer:
    """
    OOP Model Optimizer.
    Manages CV parameter tuning over search spaces, including stratified sampling and callbacks.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def stratified_sample(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        sample_size: int,
        random_state: int
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extracts a stratified sample from the training splits for faster search execution.
        """
        if sample_size >= len(X):
            self.logger.info("Sample size %d >= dataset length %d. Using full dataset.", sample_size, len(X))
            return X, y

        self.logger.info("Extracting stratified sample of %d records (out of %d total)...", sample_size, len(X))
        X_sample, _, y_sample, _ = train_test_split(
            X, y,
            train_size=sample_size,
            stratify=y,
            random_state=random_state
        )
        self.logger.debug("Sample shape resolved to: %s", X_sample.shape)
        return X_sample, y_sample

    def optimize_hyperparameters(
        self,
        model_name: str,
        estimator: Any,
        X_train_sample: pd.DataFrame,
        y_train_sample: pd.Series,
        search_method: str,
        cv_folds: int,
        n_iter: int,
        random_state: int
    ) -> Tuple[Dict[str, Any], Any]:
        """
        Runs search tuning (Grid or Randomized) over the model's search space.
        Uses StratifiedKFold CV and handles early stopping configurations.
        """
        model_key = model_name.lower().strip()
        search_space = get_search_space(model_key)
        self.logger.info("Tuning '%s' using method=%s, folds=%d...", model_name, search_method, cv_folds)

        # 1. Stratified KFold Cross-Validation Setup
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

        # 2. Early stopping validation carve-out for boosting models
        fit_params = {}
        X_search, y_search = X_train_sample, y_train_sample

        if model_key in ["lightgbm", "xgboost", "catboost"]:
            self.logger.info("Setting up early stopping validation carve-out (10%%) for '%s'...", model_key)
            try:
                X_tr, X_val, y_tr, y_val = train_test_split(
                    X_train_sample, y_train_sample,
                    test_size=0.1,
                    stratify=y_train_sample,
                    random_state=random_state
                )
                X_search, y_search = X_tr, y_tr

                if model_key == "lightgbm":
                    # Configure LightGBM early stopping
                    fit_params = {
                        "eval_set": [(X_val, y_val)],
                        "callbacks": [lgb.early_stopping(stopping_rounds=10, verbose=False)]
                    }
                elif model_key == "xgboost":
                    # Configure XGBoost early stopping
                    estimator.set_params(early_stopping_rounds=10, eval_metric="mlogloss")
                    fit_params = {
                        "eval_set": [(X_val, y_val)]
                    }
                elif model_key == "catboost":
                    # Configure CatBoost early stopping
                    fit_params = {
                        "eval_set": [(X_val, y_val)],
                        "early_stopping_rounds": 10
                    }
            except Exception as e:
                self.logger.warning("Could not set up early stopping validation split: %s. Proceeding without callbacks.", e)
                X_search, y_search = X_train_sample, y_train_sample

        # 3. Instantiate search class
        if search_method.lower() == "grid":
            search_cv = GridSearchCV(
                estimator=estimator,
                param_grid=search_space,
                cv=cv,
                n_jobs=-1,
                scoring="f1_macro",
                verbose=0
            )
        else:
            search_cv = RandomizedSearchCV(
                estimator=estimator,
                param_distributions=search_space,
                n_iter=n_iter,
                cv=cv,
                n_jobs=-1,
                random_state=random_state,
                scoring="f1_macro",
                verbose=0
            )

        # 4. Execute search fitting
        self.logger.info("Fitting search estimator on parameter combinations...")
        t0 = time.perf_counter()
        try:
            search_cv.fit(X_search, y_search, **fit_params)
        except Exception as e:
            raise ModelTrainingError(f"Hyperparameter search failed for '{model_name}': {e}") from e
        duration = time.perf_counter() - t0

        best_params = search_cv.best_params_
        best_score = search_cv.best_score_
        self.logger.info("Tuning complete in %.3f seconds. Best F1 Score: %.5f", duration, best_score)
        self.logger.info("Resolved Best Hyperparameters: %s", best_params)

        # Return best parameters and the best fitted estimator on the validation/search split
        # Note: We will refit this estimator on the full training set inside hyperparameter_tuning coordinator.
        return best_params, search_cv.best_estimator_
