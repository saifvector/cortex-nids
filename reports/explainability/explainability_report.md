# Explainable Machine Learning (XAI) Report

## Executive Summary
This report provides feature importance rankings, global SHAP explanations, and local instance-level predictions for the **Network Intrusion Detection System (NIDS)** best model (`extra_trees`).

---

## 🏆 Top 10 Most Important Features (`extra_trees`)

|   Rank | Feature                 |   Normalized_Importance |   Permutation_Importance_Mean |
|-------:|:------------------------|------------------------:|------------------------------:|
|      1 | Bwd Packet Length Max   |               0.17321   |                     0.246527  |
|      2 | Flow IAT Std            |               0.121678  |                     0.0762687 |
|      3 | Destination Port        |               0.0895642 |                     0.217678  |
|      4 | Init_Win_bytes_backward |               0.0846945 |                    -0.0483304 |
|      5 | Fwd Packet Length Max   |               0.0798738 |                     0.0310772 |
|      6 | Init_Win_bytes_forward  |               0.0654556 |                     0.218327  |
|      7 | min_seg_size_forward    |               0.063781  |                     0.168032  |
|      8 | Fwd IAT Min             |               0.050406  |                     0.053782  |
|      9 | PSH Flag Count          |               0.042431  |                     0.258248  |
|     10 | act_data_pkt_fwd        |               0.0335717 |                    -0.0705258 |

---

## 🔬 Global SHAP Feature Interpretations
- **SHAP Summary & Beeswarm**: Features with high values that push predictions toward attack categories (e.g. `Bwd Packet Length Std`, `Total Length of Fwd Packets`, `Flow Bytes/s`).
- **SHAP Bar Plot**: Quantifies mean absolute impact per feature on class log-odds / probabilities.

---

## 🎯 Instance-Level Explanations

### 1. Normal Traffic Sample Explanation
- **Status**: True
- **True Label**: `BENIGN` | **Predicted**: `BENIGN`
- **Key Characteristics**: Standard packet lengths, expected inter-arrival times, low byte transfer variance.

### 2. Attack Traffic Sample Explanation
- **Status**: True
- **True Label**: `PortScan` | **Predicted**: `PortScan`
- **Detection Rationale**: Anomalous packet count burst, elevated flow duration, or unexpected port flags trigger high attack confidence.

### 3. False Positive Explanation
- **Status**: True
- **True Label**: `BENIGN` | **Predicted**: `PortScan`
- **Explanation**: High volume benign traffic matching flood pattern heuristics.

### 4. False Negative Explanation
- **Status**: False
- **True Label**: `N/A` | **Predicted**: `N/A`
- **Explanation**: No False Negative samples in explanation subset.

---

## 🖼️ Saved Visualizations
All generated XAI figures are available in `reports/explainability/`:
- `shap_summary.png`
- `shap_bar.png`
- `shap_beeswarm.png`
- `shap_waterfall.png`
- `shap_decision.png`
- `shap_force.png`

---
*Report generated automatically by NIDS Explainable AI Pipeline.*
