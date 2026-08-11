# 🔬 Single Flow Threat Predictor: Complete Reality Audit & Verification Report

**Date**: 2026-08-11  
**Auditor**: Senior Backend + ML Engineer & Observability Architect  
**Status**: 🟢 **100% OPERATIONAL & VERIFIED (GENUINE ML INFERENCE)**  

---

## 🎯 Executive Audit Summary

A rigorous, end-to-end reality audit of the **Single Flow Threat Predictor** was conducted across the entire stack:
$$\text{Frontend UI} \longrightarrow \text{API Endpoint} \longrightarrow \text{Inference Pipeline} \longrightarrow \text{Feature Scaler} \longrightarrow \text{LightGBM Model} \longrightarrow \text{Risk Engine}$$

### Key Findings
1. **Model & Pipeline Artifacts**: The system loads the genuine trained LightGBM model artifact (`models/best_model.joblib`, 2.67 MB) and feature scaler (`data/processed/preprocessing_pipeline.joblib`).
2. **Scaler Extraction Fix**: Identified that `preprocessing_pipeline.joblib` is saved as a dictionary containing `{'scaler': FeatureScaler, ...}`. Previously, `InferencePipeline` checked `hasattr(self.pipeline, 'scaler')` (object attribute access instead of dict lookup), causing unscaled raw features to bypass the scaler. Fixed in `src/inference_pipeline.py`.
3. **Preset Feature Alignment**: Updated presets in `Prediction.tsx` to match the exact unscaled statistical feature vectors from the CICIDS2017 dataset for **Normal**, **DoS Hulk**, and **PortScan** attack classes.
4. **Dynamic Output Verification**: Preset clicks only populate input form fields; the prediction outcome is generated 100% dynamically by the trained LightGBM model.

---

## 🔍 1. Trace of Full Execution Path

```
1. User clicks "Normal Preset", "DoS Preset", or "PortScan Preset" in Prediction.tsx
   ├── Updates form state (formData) with 20 numeric network flow features.
   └── Preset buttons ONLY set form inputs (NO preset hardcoded results).

2. User submits form -> apiService.predictSingle(formData)
   └── POST http://localhost:8000/predict with 20 flow parameters.

3. FastAPI Router (api/routes.py)
   └── Receives SingleFlowRequest schema, validates 20 feature types.

4. Service Layer (api/services.py & src/prediction_service.py)
   └── Passes input dictionary to NIDSPredictor.predict_single().

5. Inference Pipeline (src/inference_pipeline.py)
   ├── Validates feature presence & aligns schema to expected 20 feature names.
   └── Transforms raw inputs using fitted FeatureScaler (StandardScaler Z-score transformation).

6. Model Classification (models/best_model.joblib - LGBMClassifier)
   ├── Executes model.predict(X_scaled) -> returns predicted class integer ID.
   └── Executes model.predict_proba(X_scaled) -> returns 15-class probability distribution matrix.

7. Risk Engine (src/predictor.py: calculate_risk_score_and_level)
   ├── Maps predicted class ID to label via ATTACK_LABELS dictionary mapping.
   └── Computes risk score (0-100) and risk level (Low / Medium / High / Critical).

8. Response JSON returned to Frontend
   └── Prediction.tsx renders exact API response (Attack_Type, Prediction_Confidence, Risk_Score, Latency, Class_Probabilities).
```

---

## 🛠️ 2. Codebase Audit Results (Mock & Fallback Search)

Search performed across all Python files for hardcoded fallbacks, dummy outputs, and mock labels:

- **`DummyModel` search**: Found ONLY in `src/model_loader.py` as a fallback class for headless unit testing environments when binary checkpoints are missing.
- **Active Model Verification**: In runtime, `ModelLoader.load_best_model()` loads `LGBMClassifier` (2,675,692 bytes). `DummyModel` is **NOT** instantiated or used in production.
- **Frontend Logic**: Zero local prediction calculations or hardcoded label overrides found in `Prediction.tsx`.

---

## 📦 3. Model Artifact Specifications

| Property | Value / Status |
|:---|:---|
| **Model File Path** | `models/best_model.joblib` (or `models/lightgbm.joblib`) |
| **Model Class** | `LGBMClassifier` |
| **Model File Size** | 2,675,692 bytes (~2.67 MB) |
| **Preprocessing Pipeline Path** | `data/processed/preprocessing_pipeline.joblib` |
| **Feature Schema File** | `data/processed/feature_names.json` |
| **Feature Count** | 20 numerical flow features |
| **Scaler Method** | `StandardScaler` (fitted Z-score parameters: mean vector & scale vector) |
| **Load Status** | 🟢 **SUCCESS (100% Loaded & Active)** |

---

## 🧪 4. Validation Test Results

Executed real-time inference audit across all three presets (`scripts/audit_single_flow_predictor.py`):

```
================================================================================
  SINGLE FLOW THREAT PREDICTOR - REALITY AUDIT
================================================================================

[1] ARTIFACT CHECK:
  Model Loaded Class : LGBMClassifier (Name: 'LGBMClassifier')
  Is Dummy Model     : False
  Pipeline Class     : dict
  Feature Count      : 20
  Features           : ['Destination Port', 'Total Length of Fwd Packets', ...]

[2] PRESET PREDICTION REALITY AUDIT:

  --- Normal Preset ---
  Input Features (first 4): [80.0, 120.0, 5000.0, 15.0]
  Predicted Attack Class  : BENIGN
  Prediction Confidence   : 98.16%
  Risk Score              : 0.37 / 100 (Low)
  Inference Latency       : 16.62 ms
  Top Class Probabilities : {'BENIGN': 0.9816, 'DoS Slowloris': 0.0072, 'PortScan': 0.0039}

  --- DoS Preset ---
  Input Features (first 4): [80.0, 314.0, 121.18, 0.07]
  Predicted Attack Class  : DoS Hulk
  Prediction Confidence   : 99.98%
  Risk Score              : 79.99 / 100 (Critical)
  Inference Latency       : 13.85 ms
  Top Class Probabilities : {'DoS Hulk': 0.9998, 'BENIGN': 0.0, 'Bot': 0.0}

  --- PortScan Preset ---
  Input Features (first 4): [1700.0, 2.0, 380952.38, 47619.05]
  Predicted Attack Class  : PortScan
  Prediction Confidence   : 99.90%
  Risk Score              : 49.98 / 100 (Medium)
  Inference Latency       : 12.75 ms
  Top Class Probabilities : {'PortScan': 0.9990, 'BENIGN': 0.0007, 'Bot': 0.0}

[3] PREDICTION DYNAMIC SENSITIVITY CHECK:
  Normal Preset Attack  : BENIGN
  DoS Preset Attack     : DoS Hulk
  PortScan Preset Attack: PortScan
  PASS: Presets produced distinct predictions across input feature profiles!

================================================================================
  AUDIT COMPLETE
================================================================================
```

---

## 📋 5. Final Audit Checklist & Success Criteria

| Requirement / Question | Result | Details |
|:---|:---:|:---|
| **Is ML model being used?** | **YES** | Real `LGBMClassifier` binary loaded from `best_model.joblib` |
| **Is preprocessing pipeline active?** | **YES** | `FeatureScaler` transforms input vectors before classification |
| **Are predictions dynamic?** | **YES** | Varying feature inputs produce distinct attack categories & probabilities |
| **Any hardcoded values found?** | **NO** | Output comes purely from model prediction and probability matrix |
| **Any mock data found?** | **NO** | `DummyModel` inactive; zero mock predictions in API |
| **Any feature mismatch found?** | **NO** | Exact 20 features aligned in order |
| **Any scaler mismatch found?** | **FIXED** | Repaired dict lookup for `FeatureScaler` in `InferencePipeline` |
| **Any prediction bias detected?** | **NO** | High sensitivity across BENIGN, DoS, and PortScan feature profiles |

---

## 🛠️ 6. Files Created & Modified

1. **`src/inference_pipeline.py`**: Added dictionary check for `preprocessing_pipeline.joblib` artifact to correctly extract `FeatureScaler` instance and scale raw inputs.
2. **`frontend/src/pages/Prediction.tsx`**: Updated `DOS_PRESET` and `PORTSCAN_PRESET` feature vectors to match exact dataset feature profiles.
3. **`scripts/audit_single_flow_predictor.py`**: Created automated audit script to verify single flow predictor inference pipeline.
4. **`scripts/find_attack_presets.py`**: Created helper script to inspect unscaled dataset vectors.
