# SOC Analyst & User Guide

Welcome to the Enterprise Network Intrusion Detection System (NIDS) Security Operations Center (SOC) Platform.

---

## 🎨 Dashboard Overview

Access the live dashboard at `http://localhost:3000` (or `http://localhost:5173`).

### Core Features:
1. **Security Posture KPI Cards**:
   - **System Threat Status**: Active operational state (`HEALTHY` / `ELEVATED` / `CRITICAL`).
   - **Threat Detection Rate**: Percentage of network flows flagged as malicious.
   - **Average Inference Latency**: Sub-millisecond latency tracker (`~20ms`).
   - **Total Processed Flows**: Counter of network flows analyzed.

2. **Live Threat Feed Widget**:
   - Displays real-time incoming alerts with source IP, destination IP, attack category, risk score, and timestamp.
   - Color-coded risk badges:
     - 🟢 **Low Risk** (0 - 25)
     - 🟡 **Medium Risk** (26 - 50)
     - 🟠 **High Risk** (51 - 75)
     - 🔴 **Critical Risk** (76 - 100)

3. **Attack Category Breakdown Chart**:
   - Visual distribution of detected attack vectors (DDoS, DoS Hulk, PortScan, Botnets, Brute Force, etc.).

4. **Live Single Flow Prediction Sandbox**:
   - Input custom flow features (Destination Port, Flow Duration, Packet Lengths) to get immediate ML predictions & risk scores.

---

## 🔍 Investigating Alerts

1. Open **Threat Feed** in the dashboard.
2. Click on any alert entry to view detailed telemetry:
   - **Class Probabilities**: Confidence score distribution across all 15 trained attack categories.
   - **5-Tuple Flow Details**: Source IP, Destination IP, Source Port, Destination Port, Protocol.
   - **SHAP Feature Impact**: Key packet features that contributed to the model's decision.
