"""
Model Trainer module for NIDS.
Handles independent model fitting, prediction profiling (latency, memory via psutil),
and computes multiclass classification metrics.
"""
import logging
import time
import psutil
from typing import Any, Dict, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from src.exceptions.custom_exceptions import ModelTrainingError


class ModelTrainer:
    """
    OOP Model Trainer.
    Fits models, measures prediction latency, profiles RAM usage, and computes metrics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.process = psutil.Process()

    def train_and_profile(
        self,
        model_name: str,
        model_instance: Any,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        class_weights: Optional[Dict[int, float]] = None,
        fit_model: bool = True
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Trains the estimator, profiles runtime statistics, and evaluates metrics.
        Can bypass the training fit step for pre-trained checkpoints.
        """
        self.logger.info("Starting training profile for: '%s'", model_name)
        stats = {}
        
        # 1. Prepare sample weights for XGBoost multiclass (if class weights are passed)
        fit_params = {}
        if model_name.lower().strip() == "xgboost" and class_weights:
            self.logger.debug("Mapping training class weights to training sample weights for XGBoost...")
            # Map y_train target classes to their respective weight values
            sample_weights = y_train.map(class_weights).values
            fit_params["sample_weight"] = sample_weights

        # 2. Fit model & profile training time/memory (or skip if already fitted)
        if fit_model:
            mem_start = self.process.memory_info().rss / (1024 * 1024)
            time_start = time.perf_counter()
            
            try:
                model_instance.fit(X_train, y_train, **fit_params)
            except Exception as e:
                raise ModelTrainingError(f"Failed to fit model '{model_name}': {e}") from e

            time_end = time.perf_counter()
            mem_end = self.process.memory_info().rss / (1024 * 1024)
            
            train_duration = time_end - time_start
            # Calculate peak memory differential safely
            mem_used = max(0.01, mem_end - mem_start)
            
            self.logger.info("Finished training '%s' in %.3f seconds. RAM used: %.2f MB", 
                             model_name, train_duration, mem_used)
        else:
            train_duration = 0.0
            mem_used = 0.0
            self.logger.info("Skipping fit step for already fitted '%s' model.", model_name)

        # 3. Profile Prediction Latency
        pred_start = time.perf_counter()
        try:
            y_pred = model_instance.predict(X_test)
        except Exception as e:
            raise ModelTrainingError(f"Model '{model_name}' failed to generate predictions: {e}") from e
        pred_end = time.perf_counter()
        pred_duration = pred_end - pred_start

        # 4. Predict Probabilities for ROC AUC
        y_prob = None
        if hasattr(model_instance, "predict_proba"):
            try:
                y_prob = model_instance.predict_proba(X_test)
            except Exception as e:
                self.logger.warning("Could not predict probabilities for '%s': %s", model_name, e)

        # 5. Evaluate Classification Metrics
        self.logger.debug("Computing performance metrics for '%s'...", model_name)
        
        # Core metrics (macro averaged for minority class reflection)
        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        recall = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

        # Multiclass ROC AUC (One-vs-Rest)
        roc_auc = 0.0
        if y_prob is not None:
            try:
                # Handle binary vs multiclass target
                n_classes = len(np.unique(y_test))
                if n_classes == 2:
                    # In binary class, y_prob[:, 1] is passed
                    roc_auc = float(roc_auc_score(y_test, y_prob[:, 1]))
                else:
                    # In multiclass, check if probability matrix matches classes
                    if y_prob.shape[1] == n_classes:
                        roc_auc = float(roc_auc_score(y_test, y_prob, multi_class="ovr", average="macro"))
                    else:
                        # Fallback to predicting subset of classes present in test split
                        present_classes = np.unique(y_test)
                        roc_auc = float(roc_auc_score(y_test, y_prob[:, present_classes], multi_class="ovr", average="macro"))
            except Exception as e:
                self.logger.warning("Failed to compute ROC AUC for '%s': %s", model_name, e)

        # Multiclass False Positive Rate (FPR)
        fpr = self._calculate_multiclass_fpr(y_test, y_pred)

        # Store stats
        stats["Accuracy"] = accuracy
        stats["Precision"] = precision
        stats["Recall"] = recall
        stats["F1 Score"] = f1
        stats["ROC AUC"] = roc_auc
        stats["False Positive Rate"] = fpr
        stats["Training Time"] = train_duration
        stats["Prediction Time"] = pred_duration
        stats["Memory Usage"] = mem_used

        self.logger.info("'%s' metrics: F1=%.4f, Recall=%.4f, FPR=%.4f", model_name, f1, recall, fpr)
        return model_instance, stats

    def _calculate_multiclass_fpr(self, y_true: Union[pd.Series, np.ndarray], y_pred: Union[pd.Series, np.ndarray]) -> float:
        """
        Calculates macro False Positive Rate across all classes from confusion matrix.
        """
        try:
            cm = confusion_matrix(y_true, y_pred)
            n_classes = cm.shape[0]
            if n_classes <= 1:
                return 0.0

            fpr_list = []
            for i in range(n_classes):
                fp = float(cm[:, i].sum() - cm[i, i])
                tn = float(cm.sum() - cm[i, :].sum() - cm[:, i].sum() + cm[i, i])
                
                denom = fp + tn
                class_fpr = (fp / denom) if denom > 0.0 else 0.0
                fpr_list.append(class_fpr)

            # Return macro average of False Positive Rates
            return float(np.mean(fpr_list))
        except Exception as e:
            self.logger.warning("Failed to compute False Positive Rate matrix: %s", e)
            return 0.0
