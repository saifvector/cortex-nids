"""
Feature Importance module for NIDS Explainable Machine Learning (XAI).
Computes tree-based feature importance, permutation importance, and partial dependence data.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance, partial_dependence
from sklearn.preprocessing import MinMaxScaler

from src.utils.utils import ensure_directory, get_absolute_path

logger = logging.getLogger(__name__)


def extract_tree_feature_importance(
    model: Any,
    feature_names: List[str]
) -> pd.DataFrame:
    """
    Extracts raw tree-based feature importance from a fitted estimator.

    Args:
        model: Fitted tree-based classifier (ExtraTrees, RandomForest, LightGBM, XGBoost, CatBoost).
        feature_names: List of feature column names.

    Returns:
        DataFrame with columns: ['Feature', 'Raw_Importance', 'Normalized_Importance', 'Rank']
    """
    importances: Optional[np.ndarray] = None

    if hasattr(model, "feature_importances_"):
        importances = np.array(model.feature_importances_)
    elif hasattr(model, "get_feature_importance"):
        # CatBoost
        importances = np.array(model.get_feature_importance())
    elif hasattr(model, "booster_"):
        # LightGBM booster
        importances = np.array(model.booster_.feature_importance(importance_type="gain"))

    if importances is None or len(importances) != len(feature_names):
        logger.warning(
            "Could not retrieve direct feature importances from model %s. Using equal weights fallback.",
            type(model).__name__
        )
        importances = np.ones(len(feature_names)) / len(feature_names)

    total_imp = np.sum(importances)
    norm_imp = importances / total_imp if total_imp > 0 else importances

    df = pd.DataFrame({
        "Feature": feature_names,
        "Raw_Importance": importances,
        "Normalized_Importance": norm_imp
    })

    df = df.sort_values(by="Normalized_Importance", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1
    return df


def compute_permutation_importance(
    model: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    feature_names: List[str],
    n_repeats: int = 5,
    random_state: int = 42,
    max_samples: int = 5000
) -> pd.DataFrame:
    """
    Computes Permutation Feature Importance on a subsample of validation/test data.

    Args:
        model: Fitted classifier.
        X_val: Feature matrix.
        y_val: Target series.
        feature_names: List of feature names.
        n_repeats: Number of times to permute a feature.
        random_state: Random state for reproducibility.
        max_samples: Maximum number of rows to evaluate for performance.

    Returns:
        DataFrame containing permutation importance means and stds.
    """
    logger.info("Computing Permutation Importance for %s (n_repeats=%d)...", type(model).__name__, n_repeats)

    if len(X_val) > max_samples:
        rng = np.random.RandomState(random_state)
        sample_idx = rng.choice(len(X_val), size=max_samples, replace=False)
        X_sub = X_val.iloc[sample_idx]
        y_sub = y_val.iloc[sample_idx]
    else:
        X_sub = X_val
        y_sub = y_val

    try:
        res = permutation_importance(
            model, X_sub, y_sub,
            scoring="f1_macro",
            n_repeats=n_repeats,
            random_state=random_state,
            n_jobs=-1
        )
        imp_means = res.importances_mean
        imp_stds = res.importances_std
    except Exception as e:
        logger.warning("Permutation importance computation failed: %s. Using zeros.", e)
        imp_means = np.zeros(len(feature_names))
        imp_stds = np.zeros(len(feature_names))

    total_perm = np.sum(np.maximum(imp_means, 0))
    norm_perm = np.maximum(imp_means, 0) / total_perm if total_perm > 0 else np.zeros_like(imp_means)

    df = pd.DataFrame({
        "Feature": feature_names,
        "Permutation_Importance_Mean": imp_means,
        "Permutation_Importance_Std": imp_stds,
        "Permutation_Normalized": norm_perm
    })

    df = df.sort_values(by="Permutation_Importance_Mean", ascending=False).reset_index(drop=True)
    df["Permutation_Rank"] = df.index + 1
    return df


def compute_partial_dependence_data(
    model: Any,
    X_val: pd.DataFrame,
    top_features: List[str],
    max_samples: int = 2000,
    grid_resolution: int = 20
) -> Dict[str, Dict[str, Any]]:
    """
    Calculates Partial Dependence Data for top features.

    Args:
        model: Fitted classifier.
        X_val: Validation dataset.
        top_features: Top feature names to analyze.
        max_samples: Subsample limit for speed.
        grid_resolution: Resolution of PDP grid.

    Returns:
        Dictionary mapping feature_name -> {'values': grid_values, 'average': pdp_averages}.
    """
    logger.info("Computing Partial Dependence Plots for top features: %s", top_features)
    if len(X_val) > max_samples:
        X_sub = X_val.sample(n=max_samples, random_state=42)
    else:
        X_sub = X_val

    pdp_results = {}
    for feat in top_features:
        if feat not in X_val.columns:
            continue
        try:
            feat_idx = list(X_val.columns).index(feat)
            res = partial_dependence(
                model, X_sub, features=[feat_idx],
                grid_resolution=grid_resolution, kind="average"
            )
            pdp_results[feat] = {
                "values": res["values"][0],
                "average": res["average"]
            }
        except Exception as e:
            logger.warning("Could not compute Partial Dependence for feature '%s': %s", feat, e)

    return pdp_results


class FeatureImportanceAnalyzer:
    """
    Analyzes and aggregates tree-based and permutation feature importances
    across multiple models.
    """

    def __init__(self, models: Dict[str, Any], feature_names: List[str]):
        self.models = models
        self.feature_names = feature_names

    def analyze_all(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        output_csv_path: Path
    ) -> pd.DataFrame:
        """
        Computes feature importances for all models, ranks them, top 10, top 20,
        and saves consolidated feature_importance.csv.

        Returns:
            Aggregated feature importance DataFrame.
        """
        combined_dfs = []

        for model_name, model in self.models.items():
            logger.info("Extracting feature importances for model: %s", model_name)
            tree_df = extract_tree_feature_importance(model, self.feature_names)
            perm_df = compute_permutation_importance(model, X_test, y_test, self.feature_names)

            merged = pd.merge(tree_df, perm_df, on="Feature")
            merged.insert(0, "Model", model_name)
            combined_dfs.append(merged)

        if combined_dfs:
            final_df = pd.concat(combined_dfs, ignore_index=True)
        else:
            final_df = pd.DataFrame()

        ensure_directory(output_csv_path.parent)
        final_df.to_csv(output_csv_path, index=False)
        logger.info("Saved combined feature importances to %s", output_csv_path)

        return final_df
