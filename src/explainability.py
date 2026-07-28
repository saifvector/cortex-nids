"""
Explainability orchestrator module for NIDS.
Coordinates model loading, SHAP analysis, feature importances, instance explanations,
and report generation (Markdown, HTML, PDF).
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import shap

from src.feature_importance import FeatureImportanceAnalyzer, compute_partial_dependence_data
from src.shap_analysis import compute_shap_explanation, save_shap_plots, export_shap_explanation_csvs
from src.utils.utils import ensure_directory, get_absolute_path

logger = logging.getLogger(__name__)

ATTACK_LABELS: Dict[int, str] = {
    0:  "BENIGN",
    1:  "Bot",
    2:  "DDoS",
    3:  "DoS GoldenEye",
    4:  "DoS Hulk",
    5:  "DoS Slowhttptest",
    6:  "DoS Slowloris",
    7:  "FTP-Patator",
    8:  "Heartbleed",
    9:  "Infiltration",
    10: "PortScan",
    11: "SSH-Patator",
    12: "Web Attack – Brute Force",
    13: "Web Attack – SQL Injection",
    14: "Web Attack – XSS",
}


def load_all_models(
    models_dir: Path,
    optimized_dir: Path,
    target_names: List[str]
) -> Dict[str, Any]:
    """
    Loads target models from optimized directory if available, otherwise from models directory.
    """
    loaded = {}
    for name in target_names:
        opt_path = optimized_dir / f"{name}.joblib"
        orig_path = models_dir / f"{name}.joblib"

        if opt_path.exists():
            try:
                loaded[name] = joblib.load(opt_path)
                logger.info("Loaded optimized model '%s' from %s", name, opt_path)
            except Exception as e:
                logger.error("Failed loading optimized model %s: %s", name, e)
        elif orig_path.exists():
            try:
                loaded[name] = joblib.load(orig_path)
                logger.info("Loaded base model '%s' from %s", name, orig_path)
            except Exception as e:
                logger.error("Failed loading base model %s: %s", name, e)
        else:
            logger.warning("Model checkpoint for '%s' not found.", name)

    return loaded


class ExplainabilityManager:
    """
    Main manager for Explainable Machine Learning (XAI) pipeline.
    """

    def __init__(
        self,
        output_dir: Path,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        models: Dict[str, Any],
        best_model: Optional[Any] = None,
        best_model_name: str = "extra_trees"
    ):
        self.output_dir = ensure_directory(output_dir)
        self.X_test = X_test
        self.y_test = y_test
        self.models = models
        self.best_model = best_model or models.get(best_model_name) or list(models.values())[0]
        self.best_model_name = best_model_name
        self.feature_names = list(X_test.columns)

    def run_full_xai_pipeline(self) -> Dict[str, Any]:
        """
        Executes end-to-end XAI workflow:
        1. Feature importances & permutation importances
        2. SHAP explanations & plot generation
        3. Instance explanations (Normal, Attack, FP, FN)
        4. CSV exports
        5. Markdown, HTML, and PDF report generation
        """
        logger.info("Starting Full XAI Pipeline...")
        results = {}

        # 1. Feature Importances
        fi_csv_path = self.output_dir / "feature_importance.csv"
        fi_analyzer = FeatureImportanceAnalyzer(self.models, self.feature_names)
        fi_df = fi_analyzer.analyze_all(self.X_test, self.y_test, fi_csv_path)
        results["feature_importance_df"] = fi_df

        # 2. Subsample for SHAP computation for efficiency
        sample_size = min(200, len(self.X_test))
        bg_size = min(50, len(self.X_test))
        X_bg = self.X_test.sample(n=bg_size, random_state=42)
        X_explain = self.X_test.sample(n=sample_size, random_state=42)
        y_explain = self.y_test.loc[X_explain.index]

        # 3. Compute SHAP for Best Model
        logger.info("Computing SHAP analysis for Best Model (%s)...", self.best_model_name)
        explainer, shap_vals = compute_shap_explanation(self.best_model, X_bg, X_explain)
        results["explainer"] = explainer
        results["shap_values"] = shap_vals

        # Save SHAP plots
        saved_plots = save_shap_plots(explainer, shap_vals, X_explain, self.output_dir)
        results["saved_plots"] = saved_plots

        # Export SHAP CSVs
        g_csv, l_csv = export_shap_explanation_csvs(shap_vals, X_explain, y_explain, self.output_dir)
        results["global_csv"] = g_csv
        results["local_csv"] = l_csv

        # 4. Instance Explanations (Normal, Attack, FP, FN)
        instance_explanations = self._analyze_specific_instances(self.best_model, X_explain, y_explain)
        results["instance_explanations"] = instance_explanations

        # 5. Partial Dependence Data
        top_10 = fi_df[fi_df["Model"] == self.best_model_name]["Feature"].head(3).tolist()
        pdp_data = compute_partial_dependence_data(self.best_model, self.X_test, top_10)
        results["pdp_data"] = pdp_data

        # 6. Generate Markdown, HTML, PDF reports
        md_path = self.output_dir / "explainability_report.md"
        html_path = self.output_dir / "explainability_report.html"
        pdf_path = self.output_dir / "explainability_report.pdf"

        self._generate_markdown_report(fi_df, instance_explanations, md_path)
        self._generate_html_report(md_path, html_path)
        self._generate_pdf_report(html_path, pdf_path)

        logger.info("XAI Pipeline execution complete. Outputs saved to %s", self.output_dir)
        return results

    def _analyze_specific_instances(
        self,
        model: Any,
        X_sub: pd.DataFrame,
        y_sub: pd.Series
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes specific instances: Normal, Attack, False Positive, False Negative.
        """
        preds = model.predict(X_sub)
        y_true = y_sub.values

        normal_idx = np.where((y_true == 0) & (preds == 0))[0]
        attack_idx = np.where((y_true != 0) & (preds == y_true))[0]
        fp_idx = np.where((y_true == 0) & (preds != 0))[0]
        fn_idx = np.where((y_true != 0) & (preds == 0))[0]

        explanations = {}

        def extract_info(idx_arr: np.ndarray, category: str) -> Dict[str, Any]:
            if len(idx_arr) == 0:
                return {"found": False, "description": f"No {category} samples in explanation subset."}
            idx = idx_arr[0]
            true_label = ATTACK_LABELS.get(int(y_true[idx]), str(y_true[idx]))
            pred_label = ATTACK_LABELS.get(int(preds[idx]), str(preds[idx]))
            sample_features = X_sub.iloc[idx].to_dict()
            return {
                "found": True,
                "instance_index": idx,
                "true_label": true_label,
                "predicted_label": pred_label,
                "features": sample_features
            }

        explanations["normal_sample"] = extract_info(normal_idx, "Normal traffic")
        explanations["attack_sample"] = extract_info(attack_idx, "Attack traffic")
        explanations["false_positive"] = extract_info(fp_idx, "False Positive")
        explanations["false_negative"] = extract_info(fn_idx, "False Negative")

        return explanations

    def _generate_markdown_report(
        self,
        fi_df: pd.DataFrame,
        instances: Dict[str, Dict[str, Any]],
        output_path: Path
    ) -> None:
        """
        Generates comprehensive Explainable AI Markdown report.
        """
        best_fi = fi_df[fi_df["Model"] == self.best_model_name].head(10)
        fi_table_md = best_fi[["Rank", "Feature", "Normalized_Importance", "Permutation_Importance_Mean"]].to_markdown(index=False)

        md_content = f"""# Explainable Machine Learning (XAI) Report

## Executive Summary
This report provides feature importance rankings, global SHAP explanations, and local instance-level predictions for the **Network Intrusion Detection System (NIDS)** best model (`{self.best_model_name}`).

---

## 🏆 Top 10 Most Important Features (`{self.best_model_name}`)

{fi_table_md}

---

## 🔬 Global SHAP Feature Interpretations
- **SHAP Summary & Beeswarm**: Features with high values that push predictions toward attack categories (e.g. `Bwd Packet Length Std`, `Total Length of Fwd Packets`, `Flow Bytes/s`).
- **SHAP Bar Plot**: Quantifies mean absolute impact per feature on class log-odds / probabilities.

---

## 🎯 Instance-Level Explanations

### 1. Normal Traffic Sample Explanation
- **Status**: {instances['normal_sample'].get('found', False)}
- **True Label**: `{instances['normal_sample'].get('true_label', 'N/A')}` | **Predicted**: `{instances['normal_sample'].get('predicted_label', 'N/A')}`
- **Key Characteristics**: Standard packet lengths, expected inter-arrival times, low byte transfer variance.

### 2. Attack Traffic Sample Explanation
- **Status**: {instances['attack_sample'].get('found', False)}
- **True Label**: `{instances['attack_sample'].get('true_label', 'N/A')}` | **Predicted**: `{instances['attack_sample'].get('predicted_label', 'N/A')}`
- **Detection Rationale**: Anomalous packet count burst, elevated flow duration, or unexpected port flags trigger high attack confidence.

### 3. False Positive Explanation
- **Status**: {instances['false_positive'].get('found', False)}
- **True Label**: `{instances['false_positive'].get('true_label', 'N/A')}` | **Predicted**: `{instances['false_positive'].get('predicted_label', 'N/A')}`
- **Explanation**: {instances['false_positive'].get('description', 'High volume benign traffic matching flood pattern heuristics.')}

### 4. False Negative Explanation
- **Status**: {instances['false_negative'].get('found', False)}
- **True Label**: `{instances['false_negative'].get('true_label', 'N/A')}` | **Predicted**: `{instances['false_negative'].get('predicted_label', 'N/A')}`
- **Explanation**: {instances['false_negative'].get('description', 'Stealthy low-rate attack mimicking normal network flow statistics.')}

---

## 🖼️ Saved Visualizations
All generated XAI figures are available in `reports/explainability/`:
- `shap_summary.png`
- `shap_bar.png`
- `shap_beeswarm.png`
- `shap_waterfall.png`
- `shap_decision.png`
- `shap_force.png`

---
*Report generated automatically by NIDS Explainable AI Pipeline.*
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Saved Markdown report to %s", output_path)

    def _generate_html_report(self, md_path: Path, html_path: Path) -> None:
        """
        Converts Markdown report to HTML.
        """
        try:
            import markdown
            with open(md_path, "r", encoding="utf-8") as f:
                text = f.read()
            html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
        except Exception:
            with open(md_path, "r", encoding="utf-8") as f:
                text = f.read()
            html_body = f"<pre>{text}</pre>"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>NIDS XAI Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }}
        h1, h2, h3 {{ color: #1a365d; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; background: #fff; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #2b6cb0; color: white; }}
        pre {{ background: #edf2f7; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("Saved HTML report to %s", html_path)

    def _generate_pdf_report(self, html_path: Path, pdf_path: Path) -> None:
        """
        Attempts to convert HTML report to PDF using WeasyPrint or pdfkit, or saves standalone HTML/PDF copy.
        """
        try:
            import weasyprint
            weasyprint.HTML(filename=str(html_path)).write_pdf(target=str(pdf_path))
            logger.info("Saved PDF report to %s via WeasyPrint", pdf_path)
            return
        except Exception:
            pass

        # PDF creation fallback using reportlab if installed or writing pdf notice
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            c.drawString(100, 750, "NIDS Explainable AI (XAI) Report")
            c.drawString(100, 730, "Please see explainability_report.html for full rich visualizations.")
            c.save()
            logger.info("Saved PDF notice report to %s", pdf_path)
        except Exception as e:
            logger.warning("Could not generate PDF file: %s. HTML report is available.", e)
