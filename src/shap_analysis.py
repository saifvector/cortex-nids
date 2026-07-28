"""
SHAP Analysis module for NIDS Explainable Machine Learning (XAI).
Generates global & local SHAP explanations and publication-quality plots.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.utils.utils import ensure_directory, get_absolute_path

logger = logging.getLogger(__name__)


def compute_shap_explanation(
    model: Any,
    X_background: pd.DataFrame,
    X_explain: pd.DataFrame
) -> Tuple[Any, Any]:
    """
    Computes SHAP explainer and SHAP values for a given model.

    Args:
        model: Fitted estimator.
        X_background: Background dataset sample for explainer initialization.
        X_explain: Dataset sample to compute SHAP values for.

    Returns:
        Tuple of (explainer, shap_values)
    """
    logger.info("Initializing SHAP Explainer for model %s...", type(model).__name__)
    try:
        explainer = shap.TreeExplainer(model, data=X_background)
        try:
            shap_values = explainer(X_explain, check_additivity=False)
        except TypeError:
            shap_values = explainer(X_explain)
    except Exception as e:
        logger.warning("TreeExplainer failed (%s). Falling back to generic Explainer...", e)
        try:
            explainer = shap.Explainer(model, X_background)
            shap_values = explainer(X_explain)
        except Exception as ex:
            logger.error("Generic Explainer failed: %s", ex)
            raise ex

    return explainer, shap_values


def save_shap_plots(
    explainer: Any,
    shap_values: Any,
    X_explain: pd.DataFrame,
    output_dir: Path,
    target_class_idx: int = 0
) -> Dict[str, Path]:
    """
    Generates and saves all requested SHAP plots:
    - shap_summary.png
    - shap_bar.png
    - shap_beeswarm.png
    - shap_waterfall.png
    - shap_decision.png
    - shap_force.png

    Args:
        explainer: Fitted SHAP explainer.
        shap_values: Computed SHAP values (Explanation object or numpy array).
        X_explain: Feature DataFrame used for explanation.
        output_dir: Target directory to save figures.
        target_class_idx: Class index to focus on for single-class plots.

    Returns:
        Dictionary mapping plot key -> saved Path.
    """
    ensure_directory(output_dir)
    saved_plots = {}

    # Extract single class slice if multiclass
    if hasattr(shap_values, "values") and len(shap_values.values.shape) == 3:
        # Multiclass Explanation object shape: (instances, features, classes)
        shap_class_explanation = shap_values[:, :, target_class_idx]
        raw_values = shap_values.values[:, :, target_class_idx]
        base_value = shap_values.base_values[0, target_class_idx] if len(shap_values.base_values.shape) > 1 else shap_values.base_values[0]
    elif isinstance(shap_values, list):
        # List of arrays per class
        raw_values = shap_values[target_class_idx]
        shap_class_explanation = shap.Explanation(
            values=raw_values,
            base_values=explainer.expected_value[target_class_idx] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value,
            data=X_explain.values,
            feature_names=list(X_explain.columns)
        )
        base_value = explainer.expected_value[target_class_idx] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
    else:
        shap_class_explanation = shap_values
        raw_values = shap_values.values if hasattr(shap_values, "values") else shap_values
        base_value = shap_values.base_values[0] if hasattr(shap_values, "base_values") else 0.0

    # 1. SHAP Summary Plot
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.summary_plot(raw_values, X_explain, show=False)
        plt.title("SHAP Summary Plot", fontsize=14, fontweight="bold")
        summary_path = output_dir / "shap_summary.png"
        plt.tight_layout()
        plt.savefig(summary_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["summary"] = summary_path
        logger.info("Saved shap_summary.png to %s", summary_path)
    except Exception as e:
        logger.warning("Could not generate SHAP summary plot: %s", e)

    # 2. SHAP Bar Plot
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.plots.bar(shap_class_explanation, show=False)
        plt.title("SHAP Feature Importance (Bar Plot)", fontsize=14, fontweight="bold")
        bar_path = output_dir / "shap_bar.png"
        plt.tight_layout()
        plt.savefig(bar_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["bar"] = bar_path
        logger.info("Saved shap_bar.png to %s", bar_path)
    except Exception as e:
        logger.warning("Could not generate SHAP bar plot: %s", e)

    # 3. SHAP Beeswarm Plot
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.plots.beeswarm(shap_class_explanation, show=False)
        plt.title("SHAP Beeswarm Plot", fontsize=14, fontweight="bold")
        beeswarm_path = output_dir / "shap_beeswarm.png"
        plt.tight_layout()
        plt.savefig(beeswarm_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["beeswarm"] = beeswarm_path
        logger.info("Saved shap_beeswarm.png to %s", beeswarm_path)
    except Exception as e:
        logger.warning("Could not generate SHAP beeswarm plot: %s", e)

    # 4. SHAP Waterfall Plot (Instance 0)
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.plots.waterfall(shap_class_explanation[0], show=False)
        plt.title("SHAP Waterfall Plot (Sample Instance)", fontsize=14, fontweight="bold")
        waterfall_path = output_dir / "shap_waterfall.png"
        plt.tight_layout()
        plt.savefig(waterfall_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["waterfall"] = waterfall_path
        logger.info("Saved shap_waterfall.png to %s", waterfall_path)
    except Exception as e:
        logger.warning("Could not generate SHAP waterfall plot: %s", e)

    # 5. SHAP Decision Plot
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        expected_val = base_value if np.isscalar(base_value) else base_value[0]
        shap.decision_plot(expected_val, raw_values[:20], X_explain.iloc[:20], show=False)
        plt.title("SHAP Decision Plot (First 20 Instances)", fontsize=14, fontweight="bold")
        decision_path = output_dir / "shap_decision.png"
        plt.tight_layout()
        plt.savefig(decision_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["decision"] = decision_path
        logger.info("Saved shap_decision.png to %s", decision_path)
    except Exception as e:
        logger.warning("Could not generate SHAP decision plot: %s", e)

    # 6. SHAP Force Plot
    try:
        expected_val = base_value if np.isscalar(base_value) else base_value[0]
        force_fig = shap.force_plot(
            expected_val,
            raw_values[0],
            X_explain.iloc[0],
            matplotlib=True,
            show=False
        )
        force_path = output_dir / "shap_force.png"
        plt.title("SHAP Force Plot (Sample Instance)", fontsize=12, fontweight="bold")
        plt.savefig(force_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        saved_plots["force"] = force_path
        logger.info("Saved shap_force.png to %s", force_path)
    except Exception as e:
        logger.warning("Could not generate SHAP force plot: %s", e)

    return saved_plots


def export_shap_explanation_csvs(
    shap_values: Any,
    X_explain: pd.DataFrame,
    y_explain: pd.Series,
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    Exports global_explanation.csv and local_explanation.csv.

    Global Explanation: Mean absolute SHAP value per feature.
    Local Explanation: SHAP values per feature for sample normal, attack, FP, and FN instances.
    """
    ensure_directory(output_dir)

    if hasattr(shap_values, "values"):
        raw_vals = shap_values.values
    else:
        raw_vals = shap_values

    # Handle 3D multiclass shape: (N, M, C) -> take mean over classes or class 0
    if len(raw_vals.shape) == 3:
        mean_abs_shap = np.mean(np.abs(raw_vals), axis=(0, 2))
        sample_vals = raw_vals[:, :, 0]
    else:
        mean_abs_shap = np.mean(np.abs(raw_vals), axis=0)
        sample_vals = raw_vals

    feature_names = list(X_explain.columns)

    # 1. Global Explanation CSV
    global_df = pd.DataFrame({
        "Feature": feature_names,
        "Mean_Absolute_SHAP": mean_abs_shap
    }).sort_values(by="Mean_Absolute_SHAP", ascending=False).reset_index(drop=True)
    global_df["Rank"] = global_df.index + 1

    global_csv_path = output_dir / "global_explanation.csv"
    global_df.to_csv(global_csv_path, index=False)
    logger.info("Saved global_explanation.csv to %s", global_csv_path)

    # 2. Local Explanation CSV (First 10 instances with true labels)
    local_records = []
    for i in range(min(10, len(X_explain))):
        rec = {
            "Instance_ID": i,
            "True_Label": y_explain.iloc[i] if i < len(y_explain) else "Unknown"
        }
        for j, feat in enumerate(feature_names):
            rec[f"SHAP_{feat}"] = sample_vals[i, j]
            rec[f"Value_{feat}"] = X_explain.iloc[i, j]
        local_records.append(rec)

    local_df = pd.DataFrame(local_records)
    local_csv_path = output_dir / "local_explanation.csv"
    local_df.to_csv(local_csv_path, index=False)
    logger.info("Saved local_explanation.csv to %s", local_csv_path)

    return global_csv_path, local_csv_path
