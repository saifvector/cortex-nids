"""
Reality Audit Script for Single Flow Threat Predictor.
Audits model loading, preprocessing pipeline, feature alignment, and preset predictions.
"""
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_loader import ModelLoader
from src.inference_pipeline import InferencePipeline
from src.predictor import NIDSPredictor, ATTACK_LABELS

# Presets from frontend Prediction.tsx
DEFAULT_INPUT = {
    'Destination Port': 80.0,
    'Total Length of Fwd Packets': 120.0,
    'Fwd Packet Length Max': 60.0,
    'Bwd Packet Length Max': 1460.0,
    'Flow Bytes/s': 5000.0,
    'Flow IAT Std': 1200.0,
    'Fwd IAT Min': 10.0,
    'Fwd Header Length': 40.0,
    'Bwd Header Length': 40.0,
    'Bwd Packets/s': 15.0,
    'FIN Flag Count': 0.0,
    'PSH Flag Count': 1.0,
    'Init_Win_bytes_forward': 8192.0,
    'Init_Win_bytes_backward': 255.0,
    'act_data_pkt_fwd': 2.0,
    'min_seg_size_forward': 20.0,
    'Active Mean': 0.0,
    'Active Std': 0.0,
    'Active Max': 0.0,
    'Idle Std': 0.0,
}

DOS_PRESET = {
    'Destination Port': 80.0,
    'Total Length of Fwd Packets': 314.0,
    'Fwd Packet Length Max': 314.0,
    'Bwd Packet Length Max': 4344.0,
    'Flow Bytes/s': 121.18,
    'Flow IAT Std': 28300000.0,
    'Fwd IAT Min': 1.0,
    'Fwd Header Length': 200.0,
    'Bwd Header Length': 232.0,
    'Bwd Packets/s': 0.07,
    'FIN Flag Count': 0.0,
    'PSH Flag Count': 0.0,
    'Init_Win_bytes_forward': 251.0,
    'Init_Win_bytes_backward': 235.0,
    'act_data_pkt_fwd': 1.0,
    'min_seg_size_forward': 32.0,
    'Active Mean': 3.0,
    'Active Std': 0.0,
    'Active Max': 3.0,
    'Idle Std': 0.0,
}

PORTSCAN_PRESET = {
    'Destination Port': 1700.0,
    'Total Length of Fwd Packets': 2.0,
    'Fwd Packet Length Max': 2.0,
    'Bwd Packet Length Max': 6.0,
    'Flow Bytes/s': 380952.38,
    'Flow IAT Std': 0.0,
    'Fwd IAT Min': 0.0,
    'Fwd Header Length': 24.0,
    'Bwd Header Length': 20.0,
    'Bwd Packets/s': 47619.05,
    'FIN Flag Count': 0.0,
    'PSH Flag Count': 1.0,
    'Init_Win_bytes_forward': 1024.0,
    'Init_Win_bytes_backward': 0.0,
    'act_data_pkt_fwd': 0.0,
    'min_seg_size_forward': 24.0,
    'Active Mean': 0.0,
    'Active Std': 0.0,
    'Active Max': 0.0,
    'Idle Std': 0.0,
}

def audit():
    print("=" * 80)
    print("  SINGLE FLOW THREAT PREDICTOR - REALITY AUDIT")
    print("=" * 80)

    # 1. ARTIFACT CHECK
    loader = ModelLoader()
    best_model, model_name = loader.load_best_model()
    pipeline = loader.load_preprocessing_pipeline()
    features = loader.load_feature_names()

    print(f"\n[1] ARTIFACT CHECK:")
    print(f"  Model Loaded Class : {type(best_model).__name__} (Name: '{model_name}')")
    print(f"  Is Dummy Model     : {type(best_model).__name__ == 'DummyModel'}")
    print(f"  Pipeline Class     : {type(pipeline).__name__}")
    print(f"  Feature Count      : {len(features)}")
    print(f"  Features           : {features}")

    predictor = NIDSPredictor()

    # 2. AUDIT PRESETS
    presets = [
        ("Normal Preset", DEFAULT_INPUT),
        ("DoS Preset", DOS_PRESET),
        ("PortScan Preset", PORTSCAN_PRESET),
    ]

    print("\n[2] PRESET PREDICTION REALITY AUDIT:")
    results = {}
    for label, inp in presets:
        res = predictor.predict_single(inp)
        results[label] = res
        print(f"\n  --- {label} ---")
        print(f"  Input Vector Values (first 4): {[inp['Destination Port'], inp['Total Length of Fwd Packets'], inp['Flow Bytes/s'], inp['Bwd Packets/s']]}")
        print(f"  Predicted Attack Class  : {res.get('Attack_Type')}")
        print(f"  Prediction Confidence   : {res.get('Prediction_Confidence') * 100:.2f}%")
        print(f"  Risk Score              : {res.get('Risk_Score')} / 100 ({res.get('Risk_Level')})")
        print(f"  Inference Latency       : {res.get('Prediction_Time_ms')} ms")
        top_probs = dict(sorted(res.get('Class_Probabilities', {}).items(), key=lambda x: x[1], reverse=True)[:3])
        print(f"  Top Class Probabilities : {top_probs}")

    # 3. VERIFY DYNAMIC PREDICTION SENSITIVITY
    pred_classes = [r["Attack_Type"] for r in results.values()]
    print("\n[3] PREDICTION DYNAMIC SENSITIVITY CHECK:")
    print(f"  Normal Preset Attack  : {results['Normal Preset']['Attack_Type']}")
    print(f"  DoS Preset Attack     : {results['DoS Preset']['Attack_Type']}")
    print(f"  PortScan Preset Attack: {results['PortScan Preset']['Attack_Type']}")

    all_same = (len(set(pred_classes)) == 1)
    if all_same:
        print(f"  WARNING: All presets produced identical prediction: '{pred_classes[0]}'")
    else:
        print(f"  PASS: Presets produced distinct predictions across input feature profiles!")

    print("\n" + "=" * 80)
    print("  AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    audit()
