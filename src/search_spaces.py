"""
Search Spaces module for NIDS Hyperparameter Optimization.
Defines parameter grids for all 5 target classifiers.
Uses names matching the scikit-learn wrapper API signatures of each package.
"""
from typing import Any, Dict


GET_SEARCH_SPACES: Dict[str, Dict[str, list]] = {
    "random_forest": {
        "n_estimators": [10, 30, 50],
        "max_depth": [10, 15, 20, None],
        "min_samples_leaf": [1, 2, 4],
        "min_samples_split": [2, 5, 10],
        "bootstrap": [True, False]
    },
    "extra_trees": {
        "n_estimators": [10, 30, 50],
        "max_depth": [10, 15, 20, None],
        "criterion": ["gini", "entropy"],
        "min_samples_leaf": [1, 2, 4]
    },
    "lightgbm": {
        "n_estimators": [30, 50, 100],
        "max_depth": [4, 6, 8],
        "num_leaves": [15, 31, 63],
        "learning_rate": [0.05, 0.1, 0.2],
        "colsample_bytree": [0.7, 0.8, 0.9],  # scikit-learn wrapper name for feature_fraction
        "subsample": [0.7, 0.8, 0.9],          # scikit-learn wrapper name for bagging_fraction
        "min_child_samples": [10, 20, 30]
    },
    "xgboost": {
        "n_estimators": [30, 50, 100],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.7, 0.8, 0.9],
        "colsample_bytree": [0.7, 0.8, 0.9],
        "gamma": [0.0, 0.1, 0.2],
        "min_child_weight": [1, 3, 5]
    },
    "catboost": {
        "iterations": [30, 50, 100],
        "depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1, 0.2],
        "l2_leaf_reg": [1, 3, 5],
        "border_count": [32, 64, 128]
    }
}


def get_search_space(model_name: str) -> Dict[str, Any]:
    """Returns the parameter search grid for the specified model key."""
    model_key = model_name.lower().strip()
    if model_key not in GET_SEARCH_SPACES:
        raise ValueError(f"No search space defined for model '{model_name}'.")
    return GET_SEARCH_SPACES[model_key]
