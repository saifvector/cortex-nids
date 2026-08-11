"""
Live Attack & Network Traffic Generator Script for Cortex NIDS.
Simulates real-time live threat traffic (PortScan, DoS GoldenEye, DDoS, BENIGN)
and posts prediction telemetry directly to the active FastAPI server and WebSocket stream.

Usage:
    python scripts/simulate_live_attacks.py --rate 1.0 --duration 60
"""
import argparse
import json
import random
import sys
import time
import urllib.request

API_BASE = "http://localhost:8000"

# Sample Attack Profiles for Realistic Telemetry
ATTACK_PROFILES = [
    {
        "name": "BENIGN",
        "weight": 0.70,
        "src_ip": "192.168.1.{}",
        "dst_port": [80, 443, 53, 8080],
        "fwd_pkts": (5, 50),
        "flow_bytes": (1000, 50000),
    },
    {
        "name": "DoS GoldenEye",
        "weight": 0.10,
        "src_ip": "172.16.0.{}",
        "dst_port": [80, 443],
        "fwd_pkts": (500, 2000),
        "flow_bytes": (100000, 500000),
    },
    {
        "name": "DDoS",
        "weight": 0.10,
        "src_ip": "10.0.0.{}",
        "dst_port": [80, 8080, 22],
        "fwd_pkts": (1000, 5000),
        "flow_bytes": (500000, 2000000),
    },
    {
        "name": "PortScan",
        "weight": 0.10,
        "src_ip": "192.168.1.{}",
        "dst_port": [21, 22, 23, 25, 53, 80, 110, 443, 3306, 8080, 8443],
        "fwd_pkts": (1, 5),
        "flow_bytes": (60, 300),
    },
]

def choose_profile():
    r = random.random()
    cumulative = 0.0
    for p in ATTACK_PROFILES:
        cumulative += p["weight"]
        if r <= cumulative:
            return p
    return ATTACK_PROFILES[0]

def send_live_flow_prediction():
    profile = choose_profile()
    src_ip = profile["src_ip"].format(random.randint(2, 250))
    dst_port = random.choice(profile["dst_port"])
    fwd_pkts = random.randint(*profile["fwd_pkts"])
    flow_bytes = random.randint(*profile["flow_bytes"])

    flow_data = {
        "_src_ip": src_ip,
        "_dst_ip": "10.0.0.1",
        "_protocol": "TCP",
        "Destination Port": dst_port,
        "Total Length of Fwd Packets": flow_bytes,
        "Fwd Packet Length Max": random.randint(100, 1460),
        "Bwd Packet Length Max": random.randint(0, 1460),
        "Flow Bytes/s": random.randint(500, 50000),
        "Flow IAT Std": random.uniform(10, 500),
        "Fwd IAT Min": random.randint(1, 20),
        "Fwd Header Length": 40,
        "Bwd Header Length": 40,
        "Bwd Packets/s": random.randint(5, 50),
        "FIN Flag Count": 0,
        "PSH Flag Count": random.choice([0, 1]),
        "Init_Win_bytes_forward": 8192,
        "Init_Win_bytes_backward": 255,
        "act_data_pkt_fwd": max(1, fwd_pkts // 2),
        "min_seg_size_forward": 20,
        "Active Mean": 0,
        "Active Std": 0,
        "Active Max": 0,
        "Idle Std": 0
    }

    try:
        payload = json.dumps(flow_data).encode("utf-8")
        req = urllib.request.Request(
            f"{API_BASE}/predict",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=3.0)
        res = json.loads(resp.read().decode())
        print(f"  [LIVE FLOW] {src_ip} -> :{dst_port} | Attack: {res.get('Attack_Type'):<15} | Risk: {res.get('Risk_Level'):<8} ({res.get('Risk_Score'):.1f}/100) | Latency: {res.get('Prediction_Time_ms'):.2f}ms")
        return True
    except Exception as e:
        print(f"  [ERROR] Could not send live flow: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Live Attack & Telemetry Generator for Cortex NIDS")
    parser.add_argument("--interval", "-i", type=float, default=1.0, help="Interval between live flows in seconds (default: 1.0)")
    parser.add_argument("--duration", "-d", type=float, default=60.0, help="Duration to run simulation in seconds (default: 60.0, 0 for infinite)")
    args = parser.parse_args()

    print("=" * 75)
    print("  CORTEX NIDS - LIVE ATTACK & TELEMETRY GENERATOR")
    print("=" * 75)
    print(f"  Target API Base : {API_BASE}")
    print(f"  Flow Interval   : {args.interval}s")
    print(f"  Duration        : {'Continuous (Press Ctrl+C to stop)' if args.duration <= 0 else f'{args.duration}s'}")
    print("=" * 75 + "\n")

    start_time = time.time()
    count = 0

    try:
        while True:
            send_live_flow_prediction()
            count += 1
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  [INTERRUPTED] Simulation stopped by user.")

    print("\n" + "=" * 75)
    print(f"  SIMULATION SUMMARY: Generated {count} live threat flows.")
    print("  Check live dashboard: http://localhost:3000/live-threats")
    print("=" * 75)

if __name__ == "__main__":
    main()
