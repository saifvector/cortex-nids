"""
Plotter module for NIDS Model Evaluation.
Generates publication-quality visualizations for confusion matrices, ROC/PR curves,
feature importance, learning curves, validation curves, and calibration curves.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from sklearn.calibration import CalibrationDisplay, calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    PrecisionRecallDisplay,
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
)
from sklearn.model_selection import learning_curve, validation_curve

logger = logging.getLogger(__name__)

# ── Colour palette ─────────────────────────────────────────────────────────────
PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B3", "#937860", "#DA8BC3", "#8C8C8C",
]
FIGURE_DPI = 150
FIGURE_SIZE_SINGLE = (10, 8)
FIGURE_SIZE_WIDE   = (14, 7)


def _save(fig: plt.Figure, path: Path, tight: bool = True) -> None:
    """Save a figure to disk and close it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if tight:
        fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Figure saved: %s", path)


# ── Confusion Matrix ───────────────────────────────────────────────────────────

def plot_confusion_matrix(
    y_true: pd.Series,
    y_pred: np.ndarray,
    model_name: str,
    output_path: Path,
    class_names: Optional[List[str]] = None,
    normalize: bool = False,
) -> None:
    """Plots and saves a confusion matrix (raw or normalized)."""
    norm = "true" if normalize else None
    title_prefix = "Normalized " if normalize else ""
    cm = confusion_matrix(y_true, y_pred, normalize=norm)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_SINGLE)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, colorbar=True, cmap="Blues", values_format=".2f" if normalize else "d")
    ax.set_title(f"{title_prefix}Confusion Matrix — {model_name}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    _save(fig, output_path)


# ── ROC Curves ────────────────────────────────────────────────────────────────

def plot_roc_curves(
    y_true: pd.Series,
    models_probs: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """Plots macro-average OvR ROC curves for all evaluated models."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    classes = np.unique(y_true)
    n_classes = len(classes)

    for idx, (name, y_prob) in enumerate(models_probs.items()):
        if y_prob is None:
            continue
        try:
            # Compute macro-average ROC by binarizing each class
            mean_fpr = np.linspace(0, 1, 200)
            tprs = []
            for i, cls in enumerate(classes):
                y_bin = (y_true == cls).astype(int)
                col = int(cls) if int(cls) < y_prob.shape[1] else i
                fpr_c, tpr_c, _ = roc_curve(y_bin, y_prob[:, col])
                tprs.append(np.interp(mean_fpr, fpr_c, tpr_c))
            mean_tpr = np.mean(tprs, axis=0)
            roc_auc = auc(mean_fpr, mean_tpr)
            ax.plot(
                mean_fpr, mean_tpr,
                color=PALETTE[idx % len(PALETTE)],
                lw=2, label=f"{name} (AUC = {roc_auc:.4f})"
            )
        except Exception as e:
            logger.warning("Could not plot ROC curve for '%s': %s", name, e)

    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random Classifier")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.02])
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("ROC Curves (Macro-Average OvR) — All Models", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    _save(fig, output_path)


# ── Precision-Recall Curves ───────────────────────────────────────────────────

def plot_precision_recall_curves(
    y_true: pd.Series,
    models_probs: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """Plots macro-average Precision-Recall curves for all evaluated models."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    classes = np.unique(y_true)

    for idx, (name, y_prob) in enumerate(models_probs.items()):
        if y_prob is None:
            continue
        try:
            mean_recall = np.linspace(0, 1, 200)
            precisions = []
            for i, cls in enumerate(classes):
                y_bin = (y_true == cls).astype(int)
                col = int(cls) if int(cls) < y_prob.shape[1] else i
                prec, rec, _ = precision_recall_curve(y_bin, y_prob[:, col])
                precisions.append(np.interp(mean_recall, rec[::-1], prec[::-1]))
            mean_prec = np.mean(precisions, axis=0)
            pr_auc_val = auc(mean_recall, mean_prec)
            ax.plot(
                mean_recall, mean_prec,
                color=PALETTE[idx % len(PALETTE)],
                lw=2, label=f"{name} (PR-AUC = {pr_auc_val:.4f})"
            )
        except Exception as e:
            logger.warning("Could not plot PR curve for '%s': %s", name, e)

    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title("Precision-Recall Curves (Macro-Average) — All Models", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    _save(fig, output_path)


# ── Feature Importance ────────────────────────────────────────────────────────

def plot_feature_importance(
    model: Any,
    feature_names: List[str],
    model_name: str,
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Plots top-N feature importances for tree-based models."""
    importances = None
    if hasattr(model, "feature_importances_"):
        importances = np.array(model.feature_importances_)
    elif hasattr(model, "get_feature_importance"):
        importances = np.array(model.get_feature_importance())

    if importances is None:
        logger.warning("Model '%s' has no feature importances. Skipping plot.", model_name)
        return

    n = min(top_n, len(feature_names))
    indices = np.argsort(importances)[-n:][::-1]
    top_features = [feature_names[i] for i in indices]
    top_importances = importances[indices]

    fig, ax = plt.subplots(figsize=(12, max(6, n // 2)))
    bars = ax.barh(range(n), top_importances[::-1], color=PALETTE[0], edgecolor="white", height=0.7)
    ax.set_yticks(range(n))
    ax.set_yticklabels(top_features[::-1], fontsize=10)
    ax.set_xlabel("Feature Importance Score", fontsize=12)
    ax.set_title(f"Top {n} Feature Importances — {model_name}", fontsize=14, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)

    # Annotate bars
    for bar, val in zip(bars, top_importances[::-1]):
        ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", ha="left", fontsize=8)

    _save(fig, output_path)


# ── Model Comparison Bar Chart ────────────────────────────────────────────────

def plot_model_comparison(
    metrics_df: pd.DataFrame,
    output_path: Path,
    metrics: Optional[List[str]] = None,
) -> None:
    """Plots a grouped bar chart comparing all models across key metrics."""
    if metrics is None:
        metrics = ["Accuracy", "F1 Score (Macro)", "Recall (Macro)", "Precision (Macro)"]

    available = [m for m in metrics if m in metrics_df.columns]
    if not available:
        logger.warning("No plottable metrics found in metrics_df. Skipping comparison plot.")
        return

    n_metrics = len(available)
    n_models = len(metrics_df)
    x = np.arange(n_models)
    width = 0.8 / n_metrics

    fig, ax = plt.subplots(figsize=(max(12, n_models * 2), 7))
    for i, metric in enumerate(available):
        offsets = x + i * width - (n_metrics - 1) * width / 2
        bars = ax.bar(
            offsets, metrics_df[metric].values, width,
            label=metric, color=PALETTE[i % len(PALETTE)], edgecolor="white"
        )
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{bar.get_height():.3f}",
                ha="center", va="bottom", fontsize=7, rotation=45
            )

    ax.set_xticks(x)
    ax.set_xticklabels(metrics_df["Model"].values, rotation=20, ha="right", fontsize=11)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.set_title("Model Performance Comparison", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)
    _save(fig, output_path)


# ── Learning Curve ────────────────────────────────────────────────────────────

def plot_learning_curve(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    output_path: Path,
    cv: int = 3,
    n_jobs: int = -1,
    sample_size: int = 20000,
) -> None:
    """Plots the learning curve (training vs. validation score vs. training size)."""
    logger.info("Generating learning curve for '%s' on a %d-record sample...", model_name, sample_size)
    try:
        # Subsample to keep it tractable
        if len(X) > sample_size:
            idx = np.random.choice(len(X), sample_size, replace=False)
            X_s, y_s = X.iloc[idx], y.iloc[idx]
        else:
            X_s, y_s = X, y

        train_sizes, train_scores, val_scores = learning_curve(
            model, X_s, y_s,
            cv=cv, n_jobs=n_jobs,
            scoring="f1_macro",
            train_sizes=np.linspace(0.1, 1.0, 8),
        )
        t_mean = np.mean(train_scores, axis=1)
        t_std  = np.std(train_scores, axis=1)
        v_mean = np.mean(val_scores, axis=1)
        v_std  = np.std(val_scores, axis=1)

        fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
        ax.plot(train_sizes, t_mean, "o-", color=PALETTE[0], label="Training Score")
        ax.fill_between(train_sizes, t_mean - t_std, t_mean + t_std, alpha=0.15, color=PALETTE[0])
        ax.plot(train_sizes, v_mean, "s-", color=PALETTE[1], label="Validation Score")
        ax.fill_between(train_sizes, v_mean - v_std, v_mean + v_std, alpha=0.15, color=PALETTE[1])
        ax.set_xlabel("Training Examples", fontsize=12)
        ax.set_ylabel("F1 Score (Macro)", fontsize=12)
        ax.set_title(f"Learning Curve — {model_name}", fontsize=14, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        _save(fig, output_path)
    except Exception as e:
        logger.warning("Could not generate learning curve for '%s': %s", model_name, e)


# ── Validation Curve ──────────────────────────────────────────────────────────

def plot_validation_curve(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    output_path: Path,
    param_name: str = "max_depth",
    param_range: Optional[List] = None,
    cv: int = 3,
    n_jobs: int = -1,
    sample_size: int = 20000,
) -> None:
    """Plots the validation curve for a hyperparameter range."""
    if param_range is None:
        param_range = [3, 5, 8, 10, 15, None]

    # Some models don't support max_depth
    if not hasattr(model, "set_params"):
        logger.warning("Model '%s' does not support set_params. Skipping validation curve.", model_name)
        return

    logger.info("Generating validation curve for '%s' on param '%s'...", model_name, param_name)
    try:
        if len(X) > sample_size:
            idx = np.random.choice(len(X), sample_size, replace=False)
            X_s, y_s = X.iloc[idx], y.iloc[idx]
        else:
            X_s, y_s = X, y

        # Filter out None values (cause issues with some models)
        valid_range = [v for v in param_range if v is not None]

        train_scores, val_scores = validation_curve(
            model, X_s, y_s,
            param_name=param_name,
            param_range=valid_range,
            cv=cv, n_jobs=n_jobs,
            scoring="f1_macro",
        )
        t_mean = np.mean(train_scores, axis=1)
        t_std  = np.std(train_scores, axis=1)
        v_mean = np.mean(val_scores, axis=1)
        v_std  = np.std(val_scores, axis=1)

        fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
        ax.plot(valid_range, t_mean, "o-", color=PALETTE[0], label="Training Score")
        ax.fill_between(valid_range, t_mean - t_std, t_mean + t_std, alpha=0.15, color=PALETTE[0])
        ax.plot(valid_range, v_mean, "s-", color=PALETTE[1], label="Validation Score")
        ax.fill_between(valid_range, v_mean - v_std, v_mean + v_std, alpha=0.15, color=PALETTE[1])
        ax.set_xlabel(param_name, fontsize=12)
        ax.set_ylabel("F1 Score (Macro)", fontsize=12)
        ax.set_title(f"Validation Curve ({param_name}) — {model_name}", fontsize=14, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        _save(fig, output_path)
    except Exception as e:
        logger.warning("Could not generate validation curve for '%s': %s", model_name, e)


# ── Calibration Curve ─────────────────────────────────────────────────────────

def plot_calibration_curves(
    y_true: pd.Series,
    models_probs: Dict[str, Optional[np.ndarray]],
    output_path: Path,
    n_bins: int = 10,
) -> None:
    """Plots calibration curves for all models (binary: BENIGN vs. attack)."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_WIDE)
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfectly Calibrated")

    for idx, (name, y_prob) in enumerate(models_probs.items()):
        if y_prob is None:
            continue
        try:
            # Use probability of class 0 (BENIGN) as the positive class for calibration
            y_bin = (y_true == 0).astype(int)
            prob_col = y_prob[:, 0] if y_prob.shape[1] > 0 else None
            if prob_col is None:
                continue
            fraction_of_pos, mean_predicted = calibration_curve(
                y_bin, prob_col, n_bins=n_bins, strategy="uniform"
            )
            ax.plot(
                mean_predicted, fraction_of_pos,
                "s-", color=PALETTE[idx % len(PALETTE)], lw=2, label=name
            )
        except Exception as e:
            logger.warning("Could not plot calibration curve for '%s': %s", name, e)

    ax.set_xlabel("Mean Predicted Probability (Class 0)", fontsize=12)
    ax.set_ylabel("Fraction of Positives (Class 0)", fontsize=12)
    ax.set_title("Calibration Curves — All Models", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    _save(fig, output_path)
