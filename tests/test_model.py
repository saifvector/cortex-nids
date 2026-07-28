"""
Unit Test Suite for Machine Learning Model Loading, Feature Alignment & Scaler Pipeline.
"""
import joblib
import numpy as np
import pandas as pd
import pytest

from src.predictor import NIDSPredictor
from src.utils.utils import get_absolute_path


def test_model_artifact_loading():
    model_path = get_absolute_path("models/best_model.joblib")
    assert model_path.exists(), f"Model file missing at {model_path}"

    model = joblib.load(model_path)
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")


def test_feature_alignment():
    predictor = NIDSPredictor()
    sample_df = pd.DataFrame([{
        "Destination Port": 443,
        "Flow Duration": 1200,
        "Total Fwd Packets": 12,
        "Total Backward Packets": 10,
        "Total Length of Fwd Packets": 600,
        "Total Length of Bwd Packets": 500,
        "Fwd Packet Length Max": 120,
        "Fwd Packet Length Min": 20,
        "Fwd Packet Length Mean": 60.0,
        "Fwd Packet Length Stddev": 12.0,
        "Bwd Packet Length Max": 100,
        "Bwd Packet Length Min": 10,
        "Bwd Packet Length Mean": 50.0,
        "Bwd Packet Length Stddev": 6.0,
        "Flow Bytes/s": 1000.0,
        "Flow Packets/s": 20.0,
        "Flow IAT Mean": 60.0,
        "Flow IAT Stddev": 6.0,
        "Flow IAT Max": 120,
        "Flow IAT Min": 1
    }])

    aligned_df = predictor.pipeline.validate_input(sample_df)
    assert aligned_df.shape[0] == 1


def test_model_predict_proba_dimensions():
    predictor = NIDSPredictor()
    sample_df = pd.DataFrame([{
        "Destination Port": 80,
        "Flow Duration": 1000,
        "Total Fwd Packets": 10,
        "Total Backward Packets": 8,
        "Total Length of Fwd Packets": 500,
        "Total Length of Bwd Packets": 400,
        "Fwd Packet Length Max": 100,
        "Fwd Packet Length Min": 20,
        "Fwd Packet Length Mean": 50.0,
        "Fwd Packet Length Stddev": 10.0,
        "Bwd Packet Length Max": 80,
        "Bwd Packet Length Min": 10,
        "Bwd Packet Length Mean": 40.0,
        "Bwd Packet Length Stddev": 5.0,
        "Flow Bytes/s": 900.0,
        "Flow Packets/s": 18.0,
        "Flow IAT Mean": 50.0,
        "Flow IAT Stddev": 5.0,
        "Flow IAT Max": 100,
        "Flow IAT Min": 1
    }])

    preds, probs = predictor.pipeline.transform_and_predict(sample_df)
    assert len(preds) == 1
    assert probs.shape[0] == 1
    assert probs.shape[1] >= 2
    assert np.isclose(np.sum(probs[0]), 1.0)
