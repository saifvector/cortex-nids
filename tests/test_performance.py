"""
Performance Benchmark Test Suite for NIDS Inference Latency & System Resources.
"""
import time
import psutil
import pytest

from src.predictor import NIDSPredictor


def test_single_inference_latency_benchmark():
    predictor = NIDSPredictor()
    sample_flow = {
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

    # Warmup
    predictor.predict_single(sample_flow)

    # Benchmark 50 iterations
    latencies = []
    for _ in range(50):
        start = time.perf_counter()
        predictor.predict_single(sample_flow)
        latencies.append((time.perf_counter() - start) * 1000)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0, f"Average prediction latency too high: {avg_latency:.2f} ms"


def test_memory_consumption_benchmark():
    process = psutil.Process()
    mem_mb = process.memory_info().rss / (1024 * 1024)
    assert mem_mb < 2048.0, f"Process memory usage too high: {mem_mb:.1f} MB"
