"""
Unit & Integration Test Suite for NIDS FastAPI Endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "project_name" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert data["prediction_engine_status"] == "active"


def test_model_info_endpoint():
    response = client.get("/model")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "accuracy" in data


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data or "requests_served" in data or "prediction_count" in data


def test_feature_importance_endpoint():
    response = client.get("/feature_importance")
    assert response.status_code == 200
    data = response.json()
    assert "top_features" in data or "feature_importances" in data


def test_alerts_endpoint():
    response = client.get("/alerts?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_threats_endpoint():
    response = client.get("/threats?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "threats" in data
    assert "providers" in data


def test_ioc_endpoint():
    response = client.get("/ioc")
    assert response.status_code == 200
    data = response.json()
    assert "whitelist" in data
    assert "blacklist" in data


def test_siem_status_endpoint():
    response = client.get("/siem/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled_connectors" in data or "active_connectors" in data or "connectors" in data


def test_mitigation_rules_endpoint():
    response = client.get("/mitigation/rules")
    assert response.status_code == 200
    data = response.json()
    assert "active_blocks_count" in data
