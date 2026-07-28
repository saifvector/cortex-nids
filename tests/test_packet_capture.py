"""
Unit Test Suite for Packet Capture, Flow Builder & Alert Storage Engine.
"""
import pytest
from src.alert_engine import AlertEngine
from src.flow_builder import FlowBuilder, NetworkFlow


def test_flow_builder_feature_extraction():
    builder = FlowBuilder()
    flow = NetworkFlow(("192.168.1.50", 54321, "10.0.0.1", 80, "TCP"), start_time=1700000000.0)

    # Simulate fake packet
    flow.add_packet("x" * 500, is_fwd=True, pkt_time=1700000000.1)

    extracted = flow.extract_features()
    assert "Destination Port" in extracted
    assert extracted["Destination Port"] == 80.0
    assert extracted["Total Length of Fwd Packets"] == 500.0


def test_alert_engine_storage_and_query():
    alert_eng = AlertEngine()

    sample_alert = {
        "id": "ALT-TEST-0001",
        "timestamp": "2026-07-28 10:00:00",
        "attack_type": "DoS Hulk",
        "confidence": 0.999,
        "risk_score": 90.0,
        "risk_level": "Critical",
        "src_ip": "185.220.101.5",
        "dst_ip": "10.0.0.1",
        "protocol": "TCP",
        "dst_port": 80,
        "prediction_time_ms": 0.05,
        "class_probabilities": {"DoS Hulk": 0.999, "BENIGN": 0.001}
    }

    alert_eng.save_alert(sample_alert)
    queried = alert_eng.query_alerts(src_ip="185.220.101.5", limit=5)
    assert len(queried) >= 1
    assert queried[0]["src_ip"] == "185.220.101.5"
    assert queried[0]["attack_type"] == "DoS Hulk"
