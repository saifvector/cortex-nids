"""
Unit and integration tests for NIDS FastAPI Backend Endpoints.
"""
import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project_name" in data
    assert data["status"] == "online"
    assert data["model_loaded"] is True


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert data["prediction_engine_status"] == "active"


def test_get_model_info():
    response = client.get("/model")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "feature_count" in data


def test_predict_single_flow():
    payload = {
        "Destination Port": 80.0,
        "Total Length of Fwd Packets": 120.0,
        "Fwd Packet Length Max": 60.0,
        "Bwd Packet Length Max": 1460.0,
        "Flow Bytes/s": 5000.0,
        "Flow IAT Std": 1200.0,
        "Fwd IAT Min": 10.0,
        "Fwd Header Length": 40.0,
        "Bwd Header Length": 40.0,
        "Bwd Packets/s": 15.0,
        "FIN Flag Count": 0.0,
        "PSH Flag Count": 1.0,
        "Init_Win_bytes_forward": 8192.0,
        "Init_Win_bytes_backward": 255.0,
        "act_data_pkt_fwd": 2.0,
        "min_seg_size_forward": 20.0,
        "Active Mean": 0.0,
        "Active Std": 0.0,
        "Active Max": 0.0,
        "Idle Std": 0.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Attack_Type" in data
    assert "Prediction_Confidence" in data
    assert "Risk_Score" in data
    assert "Risk_Level" in data


def test_get_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_served" in data
    assert "prediction_count" in data


def test_get_feature_importance():
    response = client.get("/feature_importance")
    assert response.status_code == 200
    data = response.json()
    assert "top_features" in data
    assert len(data["top_features"]) > 0


def test_batch_predict_csv():
    csv_content = """Destination Port,Total Length of Fwd Packets,Fwd Packet Length Max,Bwd Packet Length Max,Flow Bytes/s,Flow IAT Std,Fwd IAT Min,Fwd Header Length,Bwd Header Length,Bwd Packets/s,FIN Flag Count,PSH Flag Count,Init_Win_bytes_forward,Init_Win_bytes_backward,act_data_pkt_fwd,min_seg_size_forward,Active Mean,Active Std,Active Max,Idle Std
80.0,120.0,60.0,1460.0,5000.0,1200.0,10.0,40.0,40.0,15.0,0.0,1.0,8192.0,255.0,2.0,20.0,0.0,0.0,0.0,0.0
443.0,500.0,250.0,1460.0,12000.0,500.0,5.0,40.0,40.0,30.0,0.0,1.0,8192.0,255.0,4.0,20.0,0.0,0.0,0.0,0.0
"""
    files = {"file": ("test_traffic.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/batch_predict", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_records_predicted"] == 2
    assert "attack_breakdown" in data
