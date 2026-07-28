"""
Evaluator module for NIDS.
Orchestrates model loading, prediction, metrics computation, and plot generation
for all evaluated classifiers without retraining.
"""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import ModelTrainingError
from src.metrics import compute_all_metrics, build_classification_report_df
from src.plotter import (
    plot_confusion_matrix,
    plot_roc_curves,
    plot_precision_recall_curves,
    plot_feature_importance,
    plot_learning_curve,
    plot_validation_curve,
    plot_calibration_curves,
    plot_model_comparison,
)
from src.utils.utils import ensure_directory, get_absolute_path

logger = logging.getLogger(__name__)

# CICIDS2017 attack category labels (index → label)
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


def _load_model(model_path: Path, model_name: str) -> Any:
    """Loads a model checkpoint from disk."""
    if not model_path.exists():
        raise ModelTrainingError(f"Model checkpoint not found: {model_path}")
    logger.info("Loading model '%s' from: %s", model_name, model_path)
    return joblib.load(model_path)


def load_evaluation_models(
    optimized_dir: Path,
    fallback_dir: Path,
    target_names: List[str],
) -> Dict[str, Any]:
    """
    Loads evaluation models, preferring optimized checkpoints and falling back
    to original trained models when no optimized version exists.

    Args:
        optimized_dir: Path to models/optimized/.
        fallback_dir: Path to models/ (original trained models).
        target_names: List of model keys to evaluate.

    Returns:
        Dict mapping model name → fitted estimator.
    """
    models: Dict[str, Any] = {}
    for name in target_names:
        opt_path = optimized_dir / f"{name}.joblib"
        orig_path = fallback_dir / f"{name}.joblib"

        if opt_path.exists():
            try:
                models[name] = _load_model(opt_path, name)
                logger.info("Loaded optimized checkpoint for '%s'.", name)
            except Exception as e:
                logger.error("Failed to load optimized model '%s': %s", name, e)
        elif orig_path.exists():
            try:
                models[name] = _load_model(orig_path, name)
                logger.warning(
                    "No optimized checkpoint for '%s'. Using original model from %s.",
                    name, orig_path
                )
            except Exception as e:
                logger.error("Failed to load original model '%s': %s", name, e)
        else:
            logger.warning("No model checkpoint found for '%s'. Skipping evaluation.", name)

    logger.info("Loaded %d models for evaluation: %s", len(models), list(models.keys()))
    return models


class ModelEvaluator:
    """
    Orchestrates end-to-end model evaluation.
    Loads predictions, computes metrics, generates visualizations, and saves reports.
    """

    def __init__(
        self,
        output_dir: Path,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        X_train: Optional[pd.DataFrame] = None,
        y_train: Optional[pd.Series] = None,
    ) -> None:
        self.output_dir = ensure_directory(output_dir)
        self.plots_dir  = ensure_directory(output_dir / "plots")
        self.X_test  = X_test
        self.y_test  = y_test
        self.X_train = X_train
        self.y_train = y_train
        self.feature_names = list(X_test.columns)
        self.classes = sorted(y_test.unique())
        self.class_names = [ATTACK_LABELS.get(int(c), str(c)) for c in self.classes]

    def evaluate_all(
        self,
        models: Dict[str, Any],
    ) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Evaluates all provided models and returns an aggregated metrics DataFrame
        along with per-model classification report DataFrames.

        Returns:
            (metrics_df, classification_reports_dict)
        """
        all_metrics: List[Dict[str, Any]] = []
        class_reports: Dict[str, pd.DataFrame] = {}
        all_probs: Dict[str, Optional[np.ndarray]] = {}

        for name, model in models.items():
            logger.info("=" * 60)
            logger.info("Evaluating Model: %s", name)
            logger.info("=" * 60)

            # ── Predict ───────────────────────────────────────────────────
            try:
                t0 = time.perf_counter()
                y_pred = model.predict(self.X_test)
                pred_time = time.perf_counter() - t0
            except Exception as e:
                logger.error("Prediction failed for '%s': %s", name, e)
                continue

            # ── Probabilities ─────────────────────────────────────────────
            y_prob: Optional[np.ndarray] = None
            if hasattr(model, "predict_proba"):
                try:
                    y_prob = model.predict_proba(self.X_test)
                except Exception as e:
                    logger.warning("predict_proba failed for '%s': %s", name, e)

            all_probs[name] = y_prob

            # ── Metrics ───────────────────────────────────────────────────
            try:
                m = compute_all_metrics(
                    y_true=self.y_test,
                    y_pred=y_pred,
                    y_prob=y_prob,
                    model_name=name,
                    pred_time=pred_time,
                )
                all_metrics.append(m)
            except Exception as e:
                logger.error("Metrics computation failed for '%s': %s", name, e)
                continue

            # ── Classification Report ─────────────────────────────────────
            try:
                cr_df = build_classification_report_df(
                    self.y_test, y_pred, class_names=self.class_names
                )
                cr_df.insert(0, "Model", name)
                class_reports[name] = cr_df
            except Exception as e:
                logger.warning("Classification report failed for '%s': %s", name, e)

            # ── Per-model Plots ───────────────────────────────────────────
            self._generate_model_plots(name, model, y_pred)

        # ── Combined Plots ────────────────────────────────────────────────
        if all_metrics:
            metrics_df = pd.DataFrame(all_metrics)
            self._generate_combined_plots(models, all_probs, metrics_df)
            return metrics_df, class_reports

        logger.warning("No models were successfully evaluated.")
        return pd.DataFrame(), {}

    def _generate_model_plots(
        self,
        name: str,
        model: Any,
        y_pred: np.ndarray,
    ) -> None:
        """Generates per-model visualizations."""
        safe_name = name.replace(" ", "_")

        # Confusion Matrix (raw)
        try:
            plot_confusion_matrix(
                self.y_test, y_pred,
                model_name=name,
                output_path=self.plots_dir / f"{safe_name}_confusion_matrix.png",
                class_names=self.class_names,
                normalize=False,
            )
        except Exception as e:
            logger.warning("Confusion matrix plot failed for '%s': %s", name, e)

        # Confusion Matrix (normalized)
        try:
            plot_confusion_matrix(
                self.y_test, y_pred,
                model_name=name,
                output_path=self.plots_dir / f"{safe_name}_normalized_confusion_matrix.png",
                class_names=self.class_names,
                normalize=True,
            )
        except Exception as e:
            logger.warning("Normalized confusion matrix plot failed for '%s': %s", name, e)

        # Feature Importance
        try:
            plot_feature_importance(
                model=model,
                feature_names=self.feature_names,
                model_name=name,
                output_path=self.plots_dir / f"{safe_name}_feature_importance.png",
                top_n=20,
            )
        except Exception as e:
            logger.warning("Feature importance plot failed for '%s': %s", name, e)

        # Learning Curve (only when training data is available)
        if self.X_train is not None and self.y_train is not None:
            try:
                plot_learning_curve(
                    model=model,
                    X=self.X_train,
                    y=self.y_train,
                    model_name=name,
                    output_path=self.plots_dir / f"{safe_name}_learning_curve.png",
                )
            except Exception as e:
                logger.warning("Learning curve plot failed for '%s': %s", name, e)

            # Validation Curve
            try:
                # Determine supported depth param
                if hasattr(model, "max_depth"):
                    param = "max_depth"
                elif hasattr(model, "depth"):
                    param = "depth"
                else:
                    param = "n_estimators"
                plot_validation_curve(
                    model=model,
                    X=self.X_train,
                    y=self.y_train,
                    model_name=name,
                    output_path=self.plots_dir / f"{safe_name}_validation_curve.png",
                    param_name=param,
                    param_range=[5, 10, 20, 30, 50],
                )
            except Exception as e:
                logger.warning("Validation curve plot failed for '%s': %s", name, e)

    def _generate_combined_plots(
        self,
        models: Dict[str, Any],
        all_probs: Dict[str, Optional[np.ndarray]],
        metrics_df: pd.DataFrame,
    ) -> None:
        """Generates cross-model comparison visualizations."""

        # ROC Curves
        try:
            plot_roc_curves(
                y_true=self.y_test,
                models_probs={k: v for k, v in all_probs.items() if v is not None},
                output_path=self.plots_dir / "roc_curve.png",
            )
        except Exception as e:
            logger.warning("ROC curve plot failed: %s", e)

        # Precision-Recall Curves
        try:
            plot_precision_recall_curves(
                y_true=self.y_test,
                models_probs={k: v for k, v in all_probs.items() if v is not None},
                output_path=self.plots_dir / "precision_recall_curve.png",
            )
        except Exception as e:
            logger.warning("PR curve plot failed: %s", e)

        # Calibration Curves
        try:
            plot_calibration_curves(
                y_true=self.y_test,
                models_probs=all_probs,
                output_path=self.plots_dir / "calibration_curve.png",
            )
        except Exception as e:
            logger.warning("Calibration curve plot failed: %s", e)

        # Model Comparison Bar Chart
        try:
            plot_model_comparison(
                metrics_df=metrics_df,
                output_path=self.plots_dir / "model_comparison.png",
            )
        except Exception as e:
            logger.warning("Model comparison plot failed: %s", e)
