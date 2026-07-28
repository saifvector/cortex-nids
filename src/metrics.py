"""
Metrics module for NIDS Model Evaluation.
Computes comprehensive classification metrics for multiclass intrusion detection models.
"""
import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)

logger = logging.getLogger(__name__)


def compute_all_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray],
    model_name: str,
    pred_time: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes the full suite of classification metrics for a model's predictions.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted class labels.
        y_prob: Predicted class probabilities (N x C matrix), or None.
        model_name: Name of the model being evaluated.
        pred_time: Prediction latency in seconds.

    Returns:
        Dictionary of metric names to values.
    """
    logger.info("Computing comprehensive metrics for '%s'...", model_name)
    metrics: Dict[str, Any] = {"Model": model_name}

    # ── Core Accuracy ──────────────────────────────────────────────────────
    metrics["Accuracy"] = float(accuracy_score(y_true, y_pred))
    metrics["Balanced Accuracy"] = float(balanced_accuracy_score(y_true, y_pred))

    # ── Precision ──────────────────────────────────────────────────────────
    metrics["Precision (Macro)"] = float(
        precision_score(y_true, y_pred, average="macro", zero_division=0)
    )
    metrics["Precision (Weighted)"] = float(
        precision_score(y_true, y_pred, average="weighted", zero_division=0)
    )

    # ── Recall / Sensitivity ───────────────────────────────────────────────
    metrics["Recall (Macro)"] = float(
        recall_score(y_true, y_pred, average="macro", zero_division=0)
    )
    metrics["Recall (Weighted)"] = float(
        recall_score(y_true, y_pred, average="weighted", zero_division=0)
    )
    metrics["Sensitivity"] = metrics["Recall (Macro)"]  # alias

    # ── F1 Score ───────────────────────────────────────────────────────────
    metrics["F1 Score (Macro)"] = float(
        f1_score(y_true, y_pred, average="macro", zero_division=0)
    )
    metrics["F1 Score (Weighted)"] = float(
        f1_score(y_true, y_pred, average="weighted", zero_division=0)
    )

    # ── Probability-based metrics ──────────────────────────────────────────
    roc_auc = 0.0
    pr_auc = 0.0
    if y_prob is not None:
        try:
            n_classes = len(np.unique(y_true))
            classes_in_test = np.unique(y_true)
            if n_classes == 2:
                roc_auc = float(roc_auc_score(y_true, y_prob[:, 1]))
                pr_auc = float(average_precision_score(y_true, y_prob[:, 1]))
            else:
                # Align probability columns to classes present in test split
                if y_prob.shape[1] >= n_classes:
                    roc_auc = float(
                        roc_auc_score(
                            y_true,
                            y_prob[:, :n_classes],
                            multi_class="ovr",
                            average="macro",
                            labels=classes_in_test,
                        )
                    )
                    # PR-AUC: macro-average over OvR binary problems
                    pr_auc_vals = []
                    for i, cls in enumerate(classes_in_test):
                        y_bin = (y_true == cls).astype(int)
                        col_idx = int(cls) if int(cls) < y_prob.shape[1] else i
                        try:
                            pr_auc_vals.append(
                                float(average_precision_score(y_bin, y_prob[:, col_idx]))
                            )
                        except Exception:
                            pass
                    if pr_auc_vals:
                        pr_auc = float(np.mean(pr_auc_vals))
        except Exception as e:
            logger.warning("Could not compute probability-based metrics for '%s': %s", model_name, e)

    metrics["ROC-AUC (OvR)"] = roc_auc
    metrics["PR-AUC"] = pr_auc

    # ── Advanced Metrics ───────────────────────────────────────────────────
    try:
        metrics["Matthews Correlation Coefficient"] = float(matthews_corrcoef(y_true, y_pred))
    except Exception as e:
        logger.warning("Could not compute MCC for '%s': %s", model_name, e)
        metrics["Matthews Correlation Coefficient"] = 0.0

    try:
        metrics["Cohen's Kappa"] = float(cohen_kappa_score(y_true, y_pred))
    except Exception as e:
        logger.warning("Could not compute Cohen's Kappa for '%s': %s", model_name, e)
        metrics["Cohen's Kappa"] = 0.0

    # ── Confusion Matrix-derived Rates ─────────────────────────────────────
    fpr, fnr, specificity = compute_confusion_rates(y_true, y_pred)
    metrics["False Positive Rate"] = fpr
    metrics["False Negative Rate"] = fnr
    metrics["Specificity"] = specificity

    # ── Prediction Time ────────────────────────────────────────────────────
    metrics["Prediction Time (s)"] = pred_time

    logger.info(
        "'%s' → Accuracy=%.4f, F1(Macro)=%.4f, Recall(Macro)=%.4f, FPR=%.4f",
        model_name,
        metrics["Accuracy"],
        metrics["F1 Score (Macro)"],
        metrics["Recall (Macro)"],
        metrics["False Positive Rate"],
    )
    return metrics


def compute_confusion_rates(
    y_true: pd.Series, y_pred: np.ndarray
) -> Tuple[float, float, float]:
    """
    Calculates macro-averaged FPR, FNR, and Specificity from the multiclass confusion matrix.

    Returns:
        Tuple of (False Positive Rate, False Negative Rate, Specificity).
    """
    try:
        cm = confusion_matrix(y_true, y_pred)
        n = cm.shape[0]
        fpr_list, fnr_list, spec_list = [], [], []
        for i in range(n):
            tp = float(cm[i, i])
            fp = float(cm[:, i].sum() - tp)
            fn = float(cm[i, :].sum() - tp)
            tn = float(cm.sum() - tp - fp - fn)

            denom_fpr = fp + tn
            denom_fnr = tp + fn

            fpr_list.append(fp / denom_fpr if denom_fpr > 0 else 0.0)
            fnr_list.append(fn / denom_fnr if denom_fnr > 0 else 0.0)
            spec_list.append(tn / denom_fpr if denom_fpr > 0 else 0.0)

        return float(np.mean(fpr_list)), float(np.mean(fnr_list)), float(np.mean(spec_list))
    except Exception as e:
        logger.warning("Could not compute confusion rates: %s", e)
        return 0.0, 0.0, 0.0


def build_classification_report_df(
    y_true: pd.Series,
    y_pred: np.ndarray,
    class_names: Optional[list] = None,
) -> pd.DataFrame:
    """
    Generates a per-class classification report as a DataFrame.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        class_names: Optional list of human-readable class names.

    Returns:
        DataFrame with per-class precision, recall, F1, and support.
    """
    report_dict = classification_report(
        y_true, y_pred, output_dict=True, zero_division=0, target_names=class_names
    )
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.index.name = "Class"
    report_df = report_df.reset_index()
    return report_df
