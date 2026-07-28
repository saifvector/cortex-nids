"""
Integration Test Suite for React SOC Dashboard API Contracts & Data Payloads.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_dashboard_health_contract():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "healthy" in data
    assert "prediction_engine_status" in data


def test_dashboard_metrics_contract():
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_requests" in data or "requests_served" in data or "prediction_count" in data


def test_dashboard_daily_report_contract():
    res = client.get("/alerts/daily_report")
    assert res.status_code == 200
    data = res.json()
    assert "total_alerts" in data
    assert "date" in data
