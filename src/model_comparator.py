"""
Model Comparator module for NIDS.
Ranks evaluated models, highlights category leaders, and
assembles the final comparison tables and Markdown/HTML reports.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Metric columns in the order they should appear in the final comparison table
DISPLAY_METRICS: List[str] = [
    "Model",
    "Accuracy",
    "Balanced Accuracy",
    "Precision (Macro)",
    "Precision (Weighted)",
    "Recall (Macro)",
    "Recall (Weighted)",
    "F1 Score (Macro)",
    "F1 Score (Weighted)",
    "ROC-AUC (OvR)",
    "PR-AUC",
    "Matthews Correlation Coefficient",
    "Cohen's Kappa",
    "False Positive Rate",
    "False Negative Rate",
    "Specificity",
    "Sensitivity",
    "Prediction Time (s)",
]


def rank_models(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks evaluated models by F1 Score (Macro) descending, then Recall (Macro) descending,
    then False Positive Rate ascending.

    Args:
        metrics_df: DataFrame with one row per model and metric columns.

    Returns:
        Ranked DataFrame with a 'Rank' column prepended.
    """
    if metrics_df.empty:
        logger.warning("Metrics DataFrame is empty. Cannot rank models.")
        return metrics_df

    sort_cols  = ["F1 Score (Macro)", "Recall (Macro)", "False Positive Rate"]
    sort_asc   = [False, False, True]

    # Only sort on columns that actually exist
    valid = [(c, a) for c, a in zip(sort_cols, sort_asc) if c in metrics_df.columns]
    if not valid:
        logger.warning("No valid sort columns found. Returning metrics unsorted.")
        return metrics_df

    cols, asc = zip(*valid)
    ranked = metrics_df.sort_values(list(cols), ascending=list(asc)).reset_index(drop=True)
    ranked.insert(0, "Rank", ranked.index + 1)
    return ranked


def identify_leaders(ranked_df: pd.DataFrame) -> Dict[str, str]:
    """
    Identifies the best model for each key metric category.

    Returns:
        Dictionary mapping metric category label → model name.
    """
    leaders: Dict[str, str] = {}
    best_criteria = {
        "Best Accuracy":        ("Accuracy",              False),
        "Best Recall":          ("Recall (Macro)",        False),
        "Best Precision":       ("Precision (Macro)",     False),
        "Best F1":              ("F1 Score (Macro)",      False),
        "Lowest FPR":           ("False Positive Rate",   True),
        "Lowest Prediction Time": ("Prediction Time (s)", True),
        "Best ROC-AUC":         ("ROC-AUC (OvR)",         False),
        "Best MCC":             ("Matthews Correlation Coefficient", False),
    }
    for label, (col, ascending) in best_criteria.items():
        if col in ranked_df.columns and not ranked_df[col].isna().all():
            idx = ranked_df[col].idxmin() if ascending else ranked_df[col].idxmax()
            leaders[label] = ranked_df.loc[idx, "Model"]
    return leaders


def build_strengths_weaknesses(
    ranked_df: pd.DataFrame,
    leaders: Dict[str, str],
) -> Dict[str, Dict[str, List[str]]]:
    """
    Builds a per-model strengths and weaknesses summary.

    Returns:
        Dictionary mapping model name → {'strengths': [...], 'weaknesses': [...]}
    """
    summary: Dict[str, Dict[str, List[str]]] = {}
    for _, row in ranked_df.iterrows():
        name = row["Model"]
        strengths, weaknesses = [], []

        for label, leader in leaders.items():
            if leader == name:
                strengths.append(label)

        # Generic heuristics
        if row.get("Recall (Macro)", 0) >= 0.90:
            strengths.append("High intrusion recall (≥ 90%)")
        if row.get("False Positive Rate", 1.0) <= 0.001:
            strengths.append("Very low false positive rate (≤ 0.1%)")
        if row.get("Prediction Time (s)", 99) <= 1.0:
            strengths.append("Fast inference (< 1 s on full test set)")

        if row.get("F1 Score (Macro)", 0) < 0.70:
            weaknesses.append("Below-par macro F1 (< 0.70)")
        if row.get("False Positive Rate", 0) > 0.01:
            weaknesses.append("Elevated false positive rate (> 1%)")
        if row.get("Prediction Time (s)", 0) > 5.0:
            weaknesses.append("Slow inference (> 5 s on full test set)")
        if row.get("Recall (Macro)", 1) < 0.85:
            weaknesses.append("Misses some attack classes (Recall < 85%)")

        summary[name] = {"strengths": strengths or ["—"], "weaknesses": weaknesses or ["—"]}

    return summary


def generate_markdown_report(
    ranked_df: pd.DataFrame,
    leaders: Dict[str, str],
    class_reports: Dict[str, pd.DataFrame],
    strengths_weaknesses: Dict[str, Dict[str, List[str]]],
    recommended_model: str,
    output_path: Path,
    X_train_shape: tuple = (0, 0),
    X_test_shape: tuple = (0, 0),
) -> None:
    """
    Generates a comprehensive Markdown evaluation report.
    """
    # ── Helpers ────────────────────────────────────────────────────────────
    def fmt(val: Any, decimals: int = 5) -> str:
        if isinstance(val, float):
            return f"{val:.{decimals}f}"
        return str(val)

    # ── Metric comparison table ────────────────────────────────────────────
    cols = [c for c in DISPLAY_METRICS if c in ranked_df.columns]
    tbl_header = "| " + " | ".join(f"**{c}**" for c in cols) + " |"
    tbl_divider = "| " + " | ".join(":---:" if c != "Model" else ":---" for c in cols) + " |"
    tbl_rows = ""
    for _, row in ranked_df.iterrows():
        tbl_rows += "| " + " | ".join(
            f"**{row[c]}**" if c == "Model" else fmt(row[c]) for c in cols
        ) + " |\n"

    # ── Leaders table ──────────────────────────────────────────────────────
    leaders_md = "\n".join(f"| **{k}** | `{v}` |" for k, v in leaders.items())

    # ── Strengths / Weaknesses ─────────────────────────────────────────────
    sw_md = ""
    for model, sw in strengths_weaknesses.items():
        sw_md += f"\n### {model}\n"
        sw_md += "**Strengths:**\n"
        sw_md += "".join(f"- {s}\n" for s in sw["strengths"])
        sw_md += "\n**Weaknesses:**\n"
        sw_md += "".join(f"- {w}\n" for w in sw["weaknesses"])

    # ── Classification Report (best model) ────────────────────────────────
    cr_md = ""
    if recommended_model in class_reports:
        cr_df = class_reports[recommended_model]
        cr_md = cr_df.to_markdown(index=False)

    md = f"""# NIDS Model Evaluation Report

Comprehensive evaluation of optimized classifiers on the CICIDS2017 test partition.

---

## 📋 Dataset Summary
- **Train Partition**: `{X_train_shape[0]:,}` rows × `{X_train_shape[1]}` features
- **Test Partition**: `{X_test_shape[0]:,}` rows × `{X_test_shape[1]}` features

---

## 🏆 Recommended Model
> **`{recommended_model}`** — selected based on highest macro F1, high recall, and lowest FPR.

---

## 📊 Category Leaders
| Category | Best Model |
| :--- | :---: |
{leaders_md}

---

## 📈 Full Metric Comparison (Ranked)
{tbl_header}
{tbl_divider}
{tbl_rows}

---

## 🔍 Per-Model Strengths & Weaknesses
{sw_md}

---

## 📄 Classification Report — {recommended_model} (Recommended Model)
{cr_md}

---

## 📂 Plots Generated
All figures are saved in `reports/evaluation/plots/`.

| Plot | Description |
| :--- | :--- |
| `*_confusion_matrix.png` | Raw confusion matrix per model |
| `*_normalized_confusion_matrix.png` | Row-normalized confusion matrix per model |
| `roc_curve.png` | Macro-average OvR ROC curves (all models) |
| `precision_recall_curve.png` | Macro-average PR curves (all models) |
| `*_feature_importance.png` | Top-20 feature importances per model |
| `*_learning_curve.png` | Training vs. validation F1 score (learning curve) |
| `*_validation_curve.png` | Hyperparameter sensitivity curve |
| `calibration_curve.png` | Probability calibration comparison |
| `model_comparison.png` | Side-by-side metric comparison bar chart |

---
*Report generated automatically by NIDS Model Evaluation pipeline.*
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("Markdown evaluation report saved: %s", output_path)


def generate_html_report(
    markdown_path: Path,
    output_path: Path,
) -> None:
    """Converts the Markdown report to a styled HTML document."""
    try:
        import markdown as md_lib  # type: ignore
        with open(markdown_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        html_body = md_lib.markdown(
            md_text, extensions=["tables", "fenced_code", "attr_list"]
        )
    except ImportError:
        # Fallback: wrap raw markdown in a <pre> block
        with open(markdown_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        html_body = f"<pre>{md_text}</pre>"

    style = """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1200px;
               margin: 40px auto; padding: 0 24px; background: #f8f9fa; color: #212529; }
        h1 { color: #1a1a2e; border-bottom: 3px solid #4C72B0; padding-bottom: 10px; }
        h2 { color: #16213e; border-bottom: 1px solid #dee2e6; padding-bottom: 6px; }
        h3 { color: #0f3460; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px;
                font-size: 0.85em; overflow-x: auto; display: block; }
        th { background: #4C72B0; color: #fff; padding: 8px 12px; text-align: center; }
        td { padding: 6px 12px; border: 1px solid #dee2e6; }
        tr:nth-child(even) { background: #e9ecef; }
        blockquote { background: #d4edda; border-left: 4px solid #28a745;
                     padding: 10px 16px; margin: 16px 0; border-radius: 4px; }
        code { background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
        pre { background: #1a1a2e; color: #f8f8f2; padding: 16px; border-radius: 8px; overflow-x: auto; }
    </style>
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIDS Model Evaluation Report</title>
    {style}
</head>
<body>
{html_body}
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("HTML evaluation report saved: %s", output_path)
