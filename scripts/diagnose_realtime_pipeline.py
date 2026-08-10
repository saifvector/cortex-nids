"""
Real-Time Pipeline Diagnostic Script for NIDS.
Tests the complete end-to-end flow:
  1. API health check
  2. Current metrics baseline
  3. Send prediction via /predict (writes to alerts.db)
  4. Verify metrics increased
  5. Verify alerts.db row count increased
  6. Simulate live monitor DB write
  7. Verify metrics pick up external DB writes
"""
import json
import sqlite3
import sys
import time
import urllib.request

API_BASE = "http://localhost:8000"
DB_PATH = "predictions/alerts.db"

def api_get(path):
    try:
        req = urllib.request.urlopen(f"{API_BASE}{path}", timeout=5)
        return json.loads(req.read().decode())
    except Exception as e:
        return {"error": str(e)}

def api_post(path, data):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode())

def db_count():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM alerts")
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return -1

def db_insert_fake_alert():
    """Simulates what run_live_monitor.py does: writes directly to alerts.db."""
    import datetime
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now()
    alert_id = f"DIAG-{now.strftime('%Y%m%d%H%M%S')}-{int(time.time()*1000)%1000}"
    c.execute("""
        INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alert_id,
        now.strftime("%Y-%m-%d %H:%M:%S"),
        "BENIGN",
        0.9950,
        0.10,
        "Low",
        "192.168.1.200",
        "10.0.0.1",
        "ICMP",
        0,
        0.025,
        '{"BENIGN": 0.995}'
    ))
    conn.commit()
    conn.close()
    return alert_id

def run_diagnostics():
    results = []
    print("=" * 70)
    print("  NIDS REAL-TIME PIPELINE DIAGNOSTIC")
    print("=" * 70)

    # TEST 1: Health Check
    print("\n[TEST 1] API Health Check...")
    health = api_get("/health")
    if "error" in health:
        print(f"  FAIL: API not reachable: {health['error']}")
        results.append(("API Health", False))
        print("\nAPI server is not running. Start it with: .venv\\Scripts\\python.exe scripts/run_api.py")
        return
    healthy = health.get("healthy", False)
    print(f"  healthy={healthy}, engine={health.get('prediction_engine_status')}")
    results.append(("API Health", healthy))
    print(f"  {'PASS' if healthy else 'FAIL'}")

    # TEST 2: Baseline Metrics
    print("\n[TEST 2] Baseline Metrics...")
    m1 = api_get("/metrics")
    print(f"  prediction_count = {m1.get('prediction_count')}")
    print(f"  attack_count     = {m1.get('attack_count')}")
    print(f"  benign_count     = {m1.get('benign_count')}")
    print(f"  requests_served  = {m1.get('requests_served')}")
    results.append(("Metrics Endpoint", "prediction_count" in m1))
    print(f"  {'PASS' if 'prediction_count' in m1 else 'FAIL'}")

    # TEST 3: DB Baseline
    print("\n[TEST 3] SQLite alerts.db Baseline...")
    db1 = db_count()
    print(f"  Current row count: {db1}")
    results.append(("SQLite DB Accessible", db1 >= 0))
    print(f"  {'PASS' if db1 >= 0 else 'FAIL'}")

    # TEST 4: Send API Prediction
    print("\n[TEST 4] Sending POST /predict...")
    flow = {
        "Destination Port": 443,
        "Total Length of Fwd Packets": 200,
        "Fwd Packet Length Max": 100,
        "Bwd Packet Length Max": 1460,
        "Flow Bytes/s": 8000,
        "Flow IAT Std": 500,
        "Fwd IAT Min": 5,
        "Fwd Header Length": 40,
        "Bwd Header Length": 40,
        "Bwd Packets/s": 20,
        "FIN Flag Count": 0,
        "PSH Flag Count": 1,
        "Init_Win_bytes_forward": 8192,
        "Init_Win_bytes_backward": 255,
        "act_data_pkt_fwd": 3,
        "min_seg_size_forward": 20,
        "Active Mean": 0,
        "Active Std": 0,
        "Active Max": 0,
        "Idle Std": 0
    }
    pred = api_post("/predict", flow)
    print(f"  Attack_Type: {pred.get('Attack_Type')}")
    print(f"  Confidence:  {pred.get('Prediction_Confidence')}")
    print(f"  Risk_Score:  {pred.get('Risk_Score')}")
    print(f"  Risk_Level:  {pred.get('Risk_Level')}")
    print(f"  Latency:     {pred.get('Prediction_Time_ms')} ms")
    has_attack = "Attack_Type" in pred
    results.append(("ML Prediction", has_attack))
    print(f"  {'PASS' if has_attack else 'FAIL'}")

    # TEST 5: Verify DB row count increased
    print("\n[TEST 5] Verify alerts.db row count increased...")
    db2 = db_count()
    db_delta = db2 - db1
    print(f"  Before: {db1}, After: {db2}, Delta: {db_delta}")
    results.append(("DB Persistence", db_delta >= 1))
    print(f"  {'PASS' if db_delta >= 1 else 'FAIL'}")

    # TEST 6: Verify /metrics updated
    print("\n[TEST 6] Verify /metrics prediction_count increased...")
    time.sleep(2.5)  # Wait for cache to expire
    m2 = api_get("/metrics")
    pred_delta = m2.get("prediction_count", 0) - m1.get("prediction_count", 0)
    print(f"  Before: {m1.get('prediction_count')}, After: {m2.get('prediction_count')}, Delta: {pred_delta}")
    results.append(("Metrics Update (API Predict)", pred_delta >= 1))
    print(f"  {'PASS' if pred_delta >= 1 else 'FAIL'}")

    # TEST 7: Simulate external process writing to DB (like live monitor)
    print("\n[TEST 7] Simulating live_monitor DB write (external process)...")
    alert_id = db_insert_fake_alert()
    print(f"  Inserted alert: {alert_id}")
    db3 = db_count()
    print(f"  DB row count after insert: {db3}")

    # Wait for MetricsManager cache to expire (2 seconds)
    time.sleep(2.5)
    m3 = api_get("/metrics")
    ext_delta = m3.get("prediction_count", 0) - m2.get("prediction_count", 0)
    print(f"  Metrics before: {m2.get('prediction_count')}, after: {m3.get('prediction_count')}, delta: {ext_delta}")
    results.append(("External DB Write Detected", ext_delta >= 1))
    print(f"  {'PASS' if ext_delta >= 1 else 'FAIL'}")

    # TEST 8: Verify full metrics schema
    print("\n[TEST 8] Verify full /metrics response schema...")
    required_keys = [
        "prediction_count", "attack_count", "benign_count",
        "average_latency_ms", "average_confidence",
        "critical_alerts", "high_alerts", "medium_alerts", "low_alerts",
        "requests_served", "last_prediction_time"
    ]
    missing = [k for k in required_keys if k not in m3]
    all_present = len(missing) == 0
    if missing:
        print(f"  Missing keys: {missing}")
    else:
        print(f"  All 11 required fields present")
    results.append(("Full Metrics Schema", all_present))
    print(f"  {'PASS' if all_present else 'FAIL'}")

    # SUMMARY
    print("\n" + "=" * 70)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        icon = "+" if ok else "X"
        print(f"  [{icon}] {name}: {status}")
    print(f"\n  Result: {passed}/{total} tests passed")
    print("=" * 70)

    if passed == total:
        print("\n  ALL TESTS PASSED! Real-time pipeline is fully operational.")
    else:
        print("\n  SOME TESTS FAILED. See details above.")

    return passed == total


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
