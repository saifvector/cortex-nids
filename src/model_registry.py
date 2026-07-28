"""
Model Registry module for NIDS.
Maintains standard mappings between string identifiers and classifier model classes.
"""
from typing import Dict, Type
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier


# Catalog mapping of algorithm name strings to estimator classes
MODEL_REGISTRY: Dict[str, Type] = {
    "logistic_regression": LogisticRegression,
    "decision_tree": DecisionTreeClassifier,
    "random_forest": RandomForestClassifier,
    "extra_trees": ExtraTreesClassifier,
    "xgboost": XGBClassifier,
    "lightgbm": LGBMClassifier,
    "catboost": CatBoostClassifier,
}


def get_supported_models() -> list[str]:
    """Returns a list of all model identifier keys supported by the registry."""
    return list(MODEL_REGISTRY.keys())
