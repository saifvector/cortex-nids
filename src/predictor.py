"""
Predictor Engine module for NIDS.
Performs single, batch, and CSV predictions, calculating Attack Type, Prediction Confidence,
Class Probabilities, Risk Scores (0-100), Risk Levels (Low/Medium/High/Critical), and Latency (ms).
"""
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.exceptions.custom_exceptions import DataPreprocessingError, ModelTrainingError
from src.inference_pipeline import InferencePipeline
from src.utils.utils import get_absolute_path

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

# Severity weight (0 - 100) per attack category
ATTACK_SEVERITY_WEIGHTS: Dict[str, float] = {
    "BENIGN": 0.0,
    "Bot": 85.0,
    "DDoS": 90.0,
    "DoS GoldenEye": 80.0,
    "DoS Hulk": 80.0,
    "DoS Slowhttptest": 75.0,
    "DoS Slowloris": 75.0,
    "FTP-Patator": 70.0,
    "Heartbleed": 100.0,
    "Infiltration": 95.0,
    "PortScan": 50.0,
    "SSH-Patator": 90.0,
    "Web Attack – Brute Force": 65.0,
    "Web Attack – SQL Injection": 95.0,
    "Web Attack – XSS": 75.0,
}


def calculate_risk_score_and_level(
    attack_type: str,
    confidence: float,
    low_thresh: float = 25.0,
    med_thresh: float = 50.0,
    high_thresh: float = 75.0
) -> Tuple[float, str]:
    """
    Computes numerical Risk Score (0-100) and categorizes into Risk Level.

    Args:
        attack_type: Name of predicted attack or BENIGN.
        confidence: Prediction confidence probability (0.0 to 1.0).
        low_thresh: Threshold for Medium risk.
        med_thresh: Threshold for High risk.
        high_thresh: Threshold for Critical risk.

    Returns:
        Tuple of (risk_score_float, risk_level_string).
    """
    base_severity = ATTACK_SEVERITY_WEIGHTS.get(attack_type, 75.0)

    if attack_type == "BENIGN":
        # Low background noise risk
        risk_score = float(np.round((1.0 - confidence) * 20.0, 2))
    else:
        # Attack risk score scales with severity and model confidence
        risk_score = float(np.round(base_severity * (0.5 + 0.5 * confidence), 2))

    risk_score = max(0.0, min(100.0, risk_score))

    if risk_score < low_thresh:
        risk_level = "Low"
    elif risk_score < med_thresh:
        risk_level = "Medium"
    elif risk_score < high_thresh:
        risk_level = "High"
    else:
        risk_level = "Critical"

    return risk_score, risk_level


class NIDSPredictor:
    """
    Production-ready NIDS Prediction Engine.
    Supports single prediction, batch prediction, and CSV batch processing.
    """

    def __init__(
        self,
        inference_pipeline: Optional[InferencePipeline] = None,
        model_name: str = "best_model"
    ):
        if inference_pipeline is None:
            inference_pipeline = InferencePipeline.load_default()
        self.pipeline = inference_pipeline
        self.model_name = model_name

    def predict_single(self, data: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """
        Executes inference for a single network packet/flow record.

        Args:
            data: Single record dictionary or pandas Series.

        Returns:
            Dictionary containing prediction outputs and risk scores.
        """
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, pd.Series):
            df = pd.DataFrame([data.to_dict()])
        else:
            raise DataPreprocessingError(f"Unsupported data type for predict_single: {type(data)}")

        results_df = self.predict_batch(df)
        return results_df.iloc[0].to_dict()

    def predict_batch(self, data: Union[List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
        """
        Executes inference for a batch of network packet/flow records.

        Args:
            data: List of record dictionaries or pandas DataFrame.

        Returns:
            DataFrame containing all predictions, confidences, probabilities, risk scores, and latency.
        """
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise DataPreprocessingError(f"Unsupported data type for predict_batch: {type(data)}")

        t0 = time.perf_counter()
        preds, probs = self.pipeline.transform_and_predict(df)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        per_record_ms = latency_ms / max(1, len(df))

        results = []
        for i in range(len(df)):
            raw_pred = preds[i]
            attack_type = ATTACK_LABELS.get(int(raw_pred), str(raw_pred))

            if probs is not None and i < len(probs):
                row_probs = probs[i]
                confidence = float(np.max(row_probs))
                class_probs = {
                    ATTACK_LABELS.get(idx, str(idx)): float(np.round(p, 4))
                    for idx, p in enumerate(row_probs)
                }
            else:
                confidence = 1.0
                class_probs = {attack_type: 1.0}

            risk_score, risk_level = calculate_risk_score_and_level(attack_type, confidence)

            results.append({
                "Attack_Type": attack_type,
                "Prediction_Confidence": confidence,
                "Risk_Score": risk_score,
                "Risk_Level": risk_level,
                "Class_Probabilities": class_probs,
                "Model_Name": self.model_name,
                "Prediction_Time_ms": float(np.round(per_record_ms, 3))
            })

        res_df = pd.DataFrame(results)
        return res_df

    def predict_csv(
        self,
        csv_path: Union[str, Path],
        batch_size: int = 10000
    ) -> pd.DataFrame:
        """
        Executes batch inference on a CSV file, processing in chunks for memory safety.

        Args:
            csv_path: Path to CSV input file.
            batch_size: Number of records to read per chunk.

        Returns:
            Concatenated predictions DataFrame.
        """
        abs_path = get_absolute_path(csv_path)
        logger.info("Starting CSV batch prediction on: %s", abs_path)

        all_results = []
        chunk_idx = 0
        for chunk in pd.read_csv(abs_path, chunksize=batch_size):
            chunk_idx += 1
            logger.debug("Processing CSV chunk %d (%d records)...", chunk_idx, len(chunk))
            chunk_res = self.predict_batch(chunk)
            all_results.append(chunk_res)

        final_df = pd.concat(all_results, ignore_index=True)
        logger.info("Batch CSV prediction complete. Total records predicted: %d", len(final_df))
        return final_df
