"""
Prediction Service module for NIDS.
Coordinates model loading, inference execution, metadata version tracking,
prediction file exports (CSV/JSON), and markdown/HTML report generation.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np

from src.model_loader import ModelLoader
from src.inference_pipeline import InferencePipeline
from src.predictor import NIDSPredictor
from src.utils.utils import ensure_directory, get_absolute_path, save_json

logger = logging.getLogger(__name__)


class PredictionService:
    """
    High-level Prediction Service managing full prediction lifecycle:
    input validation, batch inference, output persistence, and summary report generation.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "predictions",
        model_name: Optional[str] = None
    ):
        self.output_dir = ensure_directory(output_dir)
        self.loader = ModelLoader()

        if model_name:
            self.model = self.loader.load_specific_model(model_name)
            self.model_name = model_name
        else:
            self.model, self.model_name = self.loader.load_best_model()

        self.preprocessing_pipeline = self.loader.load_preprocessing_pipeline()
        self.feature_names = self.loader.load_feature_names()
        self.metadata = self.loader.load_metadata()

        self.inference_pipeline = InferencePipeline(
            preprocessing_pipeline=self.preprocessing_pipeline,
            expected_features=self.feature_names,
            model=self.model
        )
        self.predictor = NIDSPredictor(
            inference_pipeline=self.inference_pipeline,
            model_name=self.model_name
        )

    def run_prediction_pipeline(
        self,
        input_source: Union[str, Path, pd.DataFrame],
        batch_size: int = 10000
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes prediction pipeline on CSV file or DataFrame input.
        Saves prediction_results.csv, prediction_summary.json, prediction_report.md, and prediction_report.html.

        Args:
            input_source: CSV file path or pandas DataFrame.
            batch_size: Chunk size for large CSV file processing.

        Returns:
            Tuple of (predictions DataFrame, summary Dict).
        """
        logger.info("Starting Prediction Service pipeline execution...")

        if isinstance(input_source, (str, Path)):
            predictions_df = self.predictor.predict_csv(input_source, batch_size=batch_size)
        elif isinstance(input_source, pd.DataFrame):
            predictions_df = self.predictor.predict_batch(input_source)
        else:
            raise ValueError(f"Invalid input_source type: {type(input_source)}")

        # Save prediction_results.csv
        results_path = self.output_dir / "prediction_results.csv"
        # Export core columns cleanly to CSV
        export_df = predictions_df.copy()
        export_df["Class_Probabilities"] = export_df["Class_Probabilities"].apply(json.dumps)
        export_df.to_csv(results_path, index=False)
        logger.info("Saved prediction results CSV to: %s", results_path)

        # Build prediction_summary.json
        summary = self._compile_summary(predictions_df)
        summary_path = self.output_dir / "prediction_summary.json"
        save_json(summary, summary_path)
        logger.info("Saved prediction summary JSON to: %s", summary_path)

        # Generate Reports
        md_path = self.output_dir / "prediction_report.md"
        html_path = self.output_dir / "prediction_report.html"
        self._generate_markdown_report(summary, md_path)
        self._generate_html_report(md_path, html_path)

        logger.info("Prediction Service pipeline completed successfully.")
        return predictions_df, summary

    def _compile_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compiles summary statistics and model versioning metadata.
        """
        total = len(df)
        attack_counts = df["Attack_Type"].value_counts().to_dict()
        risk_counts = df["Risk_Level"].value_counts().to_dict()

        avg_confidence = float(np.round(df["Prediction_Confidence"].mean(), 4)) if total > 0 else 0.0
        avg_risk_score = float(np.round(df["Risk_Score"].mean(), 2)) if total > 0 else 0.0
        avg_latency = float(np.round(df["Prediction_Time_ms"].mean(), 3)) if total > 0 else 0.0

        summary = {
            "model_versioning": {
                "model_name": self.model_name,
                "model_version": self.metadata.get("model_version", "1.0.0"),
                "training_date": self.metadata.get("training_date", "N/A"),
                "dataset_version": self.metadata.get("dataset_version", "CICIDS2017"),
                "feature_count": len(self.feature_names),
                "model_type": getattr(self.model, "__class__", type(self.model)).__name__
            },
            "inference_metrics": {
                "total_records_predicted": total,
                "average_confidence": avg_confidence,
                "average_risk_score": avg_risk_score,
                "average_latency_ms": avg_latency
            },
            "attack_breakdown": {str(k): int(v) for k, v in attack_counts.items()},
            "risk_level_breakdown": {str(k): int(v) for k, v in risk_counts.items()}
        }
        return summary

    def _generate_markdown_report(self, summary: Dict[str, Any], output_path: Path) -> None:
        """
        Generates prediction summary Markdown report.
        """
        mv = summary["model_versioning"]
        im = summary["inference_metrics"]
        ab = summary["attack_breakdown"]
        rb = summary["risk_level_breakdown"]

        attack_md = "\n".join(f"| `{k}` | **{v:,}** |" for k, v in ab.items())
        risk_md = "\n".join(f"| **{k}** | `{v:,}` |" for k, v in rb.items())

        md_content = f"""# NIDS Prediction Engine Report

## 📌 Model Versioning Metadata
- **Model Name**: `{mv['model_name']}` (`{mv['model_type']}`)
- **Model Version**: `{mv['model_version']}`
- **Training Date**: `{mv['training_date']}`
- **Dataset Version**: `{mv['dataset_version']}`
- **Feature Count**: `{mv['feature_count']}`

---

## ⚡ Inference Performance Metrics
- **Total Records Predicted**: `{im['total_records_predicted']:,}`
- **Average Prediction Confidence**: `{im['average_confidence']:.4f}`
- **Average Risk Score**: `{im['average_risk_score']:.2f} / 100`
- **Average Latency**: `{im['average_latency_ms']:.3f} ms / record`

---

## 🚨 Attack Category Breakdown
| Attack Type | Record Count |
| :--- | :---: |
{attack_md}

---

## 🛡️ Risk Level Distribution
| Risk Level | Record Count |
| :--- | :---: |
{risk_md}

---
*Report generated automatically by NIDS Prediction Service Engine.*
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Saved Markdown prediction report to: %s", output_path)

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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NIDS Prediction Engine Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; background: #f8f9fa; color: #212529; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #28a745; padding-bottom: 8px; }}
        h2 {{ color: #16213e; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 0.9em; }}
        th {{ background: #28a745; color: white; padding: 8px 12px; text-align: center; }}
        td {{ padding: 6px 12px; border: 1px solid #dee2e6; }}
        tr:nth-child(even) {{ background: #e9ecef; }}
        code {{ background: #e9ecef; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("Saved HTML prediction report to: %s", html_path)
