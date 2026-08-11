"""
Find exact unscaled feature values for BENIGN, DoS, and PortScan attack classes.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.predictor import ATTACK_LABELS

def main():
    X_test = pd.read_csv("data/processed/X_test.csv")
    y_test = pd.read_csv("data/processed/y_test.csv")
    p = joblib.load("data/processed/preprocessing_pipeline.joblib")
    scaler = p["scaler"]
    model = joblib.load("models/best_model.joblib")

    # Inverse transform to get raw feature numbers before scaling
    unscaled_arr = scaler.scaler.inverse_transform(X_test.values)
    unscaled_df = pd.DataFrame(unscaled_arr, columns=X_test.columns)

    preds = model.predict(X_test.values)

    print("Model Predictions Value Counts:")
    unique, counts = np.unique(preds, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"  Class {u} ({ATTACK_LABELS.get(u, 'Unknown')}): {c} samples")

    print("\n--- SAMPLE RAW INPUT VECTORS FOR PRESETS ---")
    for cls_id in [0, 3, 4, 10]:
        indices = np.where(preds == cls_id)[0]
        if len(indices) > 0:
            idx = indices[0]
            raw_row = unscaled_df.iloc[idx].to_dict()
            print(f"\nClass {cls_id} ({ATTACK_LABELS.get(cls_id)}):")
            print("{")
            for k, v in raw_row.items():
                print(f"  '{k}': {round(v, 2)},")
            print("}")

if __name__ == "__main__":
    main()
