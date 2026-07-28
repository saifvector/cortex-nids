"""
Unit Test Suite for NIDS Prediction Engine & Risk Score Calculation.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.predictor import NIDSPredictor

client = TestClient(app)


def test_predictor_initialization():
    predictor = NIDSPredictor()
    assert predictor.pipeline is not None
    assert predictor.model_name == "best_model"


def test_predict_single_flow_schema():
    payload = {
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
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "attack_type" in data or "Attack_Type" in data
    assert "confidence" in data or "Prediction_Confidence" in data
    assert "risk_score" in data or "Risk_Score" in data
    assert "risk_level" in data or "Risk_Level" in data


def test_risk_score_logic():
    predictor = NIDSPredictor()
    result = predictor.predict_single({
        "Destination Port": 80,
        "Flow Duration": 500,
        "Total Fwd Packets": 5,
        "Total Backward Packets": 5,
        "Total Length of Fwd Packets": 200,
        "Total Length of Bwd Packets": 200,
        "Fwd Packet Length Max": 50,
        "Fwd Packet Length Min": 10,
        "Fwd Packet Length Mean": 25.0,
        "Fwd Packet Length Stddev": 5.0,
        "Bwd Packet Length Max": 50,
        "Bwd Packet Length Min": 10,
        "Bwd Packet Length Mean": 25.0,
        "Bwd Packet Length Stddev": 5.0,
        "Flow Bytes/s": 400.0,
        "Flow Packets/s": 10.0,
        "Flow IAT Mean": 25.0,
        "Flow IAT Stddev": 2.0,
        "Flow IAT Max": 50,
        "Flow IAT Min": 1
    })

    assert "Risk_Score" in result or "risk_score" in result
    assert "Class_Probabilities" in result or "class_probabilities" in result
