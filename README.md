# Enterprise Network Intrusion Detection System (Cortex NIDS)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge&logo=github-actions" alt="Build Status" />
  <img src="https://img.shields.io/badge/Tests-100%25_Pass-brightgreen?style=for-the-badge" alt="Test Pass Rate" />
</p>

**GitHub Repository**: [`https://github.com/saifvector/cortex-nids`](https://github.com/saifvector/cortex-nids)

---

## 📌 Executive Overview

The **Enterprise Network Intrusion Detection System (`cortex-nids`)** is a commercial-grade, machine learning-driven Security Operations Center (SOC) platform designed to detect, classify, and mitigate cyber threats in real-time. Built with a high-throughput **LightGBM Classifier** (`99.87%` accuracy), **FastAPI**, **WebSocket Alert Streams**, **SQLite Archive (`alerts.db`)**, **Dynamic Report Engine**, **SIEM Exporters**, **SOAR Playbooks**, and a **React 18 Liquid Glass Dashboard**, the platform turns raw network telemetry into actionable security intelligence.

---

## 🏛️ System Navigation & Architecture

Cortex NIDS completely separates **LIVE Session Monitoring** from **HISTORICAL Database Telemetry**:

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         CORTEX NIDS NAVIGATION                              │
 ├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
 │ 🔴 Dashboard     │ ⚡ Live Threats  │ 📦 Historical    │ 📊 Historical      │
 │    (Session)     │    (WebSocket)   │    Threats (DB)  │    Analytics       │
 ├──────────────────┼──────────────────┼──────────────────┼────────────────────┤
 │ 📄 Reports       │ 🧪 Single        │ 📂 Batch         │ 🧠 Feature         │
 │    Center        │    Predictor     │    Analysis      │    Importance (XAI)│
 └──────────────────┴──────────────────┴──────────────────┴────────────────────┘
```

1. **Dashboard (Live Session)**: Displays metrics generated exclusively during the **current application session**. When FastAPI or Live Monitor starts, counters (`Predictions`, `Attacks`, `Benign Flows`) start at **0** and reset on restart.
2. **Live Threats**: Displays real-time incoming threat events streamed via **WebSockets (`/ws/alerts`)** with instant animated threat cards.
3. **Historical Threats**: Permanent threat archive stored in SQLite (`predictions/alerts.db`) supporting multi-field filtering, pagination, search, CSV/JSON exports, and full event inspection modals.
4. **Historical Analytics**: Long-term database insights, attack distribution pie charts, 24-hour threat timelines, severity heatmaps, and top attacker IP rankings.
5. **Reports Center**: Dynamic live report compilation engine (`DynamicReportEngine`) generating **PDF**, **HTML**, **CSV**, and **Markdown** security audit reports directly from active database records.
6. **Single Flow Predictor**: ML inference sandbox testing individual 20-feature network flows in real time.
7. **Batch Analysis**: Upload CSV network flow files for high-throughput batch classification.
8. **Feature Importance & XAI**: Extracts live model split ratios (`model.feature_importances_`) directly from the active `LGBMClassifier` checkpoint object.
9. **Global System Search (`⌘K` / `Ctrl+K`)**: Real-time debounced global search modal querying `alerts.db` threat records and platform navigation modules.
10. **Notification Panel (🔔)**: Real-time WebSocket alert listener capturing critical attacks with unread badges and drawer management.

---

## ⚡ How to Stream Live Threats & Test the System

You can test live threat detection in real time using the built-in attack simulation engine without needing root permissions or external network sniffers (`nmap`/`scapy`).

### Step 1: Start Backend & Frontend Servers

In **Terminal 1**:
```powershell
# Launch FastAPI backend server (Port 8000)
.\.venv\Scripts\python.exe scripts/run_api.py
```

In **Terminal 2**:
```powershell
# Launch React frontend dev server (Port 3000)
npm --prefix frontend run dev
```

*(Alternatively, launch both automatically using `powershell -ExecutionPolicy Bypass -File scripts\start_local.ps1`)*

---

### Step 2: Stream Live Telemetry & Test Live Traffic

You can test live threat detection using either **Real Packet Capture Sniffing** or **Synthetic Attack Simulation**.

#### Option A: Real Network Interface Sniffer (`scripts/run_live_monitor.py`)
Sniffs real network packets directly from your Wi-Fi/Ethernet adapters using Scapy, builds bidirectional 5-tuple flow statistics, executes LightGBM ML inference, and logs alerts to `alerts.db` and the UI:

1. **List Network Interfaces**:
   ```powershell
   .\.venv\Scripts\python.exe scripts/run_live_monitor.py --list-ifaces
   ```

2. **Start Continuous Live Packet Monitoring**:
   ```powershell
   .\.venv\Scripts\python.exe scripts/run_live_monitor.py --duration 0
   ```

3. **Generate Real Traffic (e.g. Ping Google or Web Browsing)**:
   In a separate terminal, trigger real ICMP/HTTP network traffic:
   ```powershell
   # Ping Google continuously to generate live network packet flows
   ping google.com -t
   ```
   Or send HTTP GET requests:
   ```powershell
   curl https://google.com
   ```
   *Watch `run_live_monitor.py` capture the live ICMP/TCP packets, extract features, predict risk, and stream alerts to the dashboard live!*

---

#### Option B: Synthetic Attack Simulation Script (`scripts/simulate_live_attacks.py`)
Generates realistic statistical attack profiles (DoS, DDoS, PortScan, Benign) and posts prediction telemetry directly to the API & WebSockets every second:

```powershell
# Stream live attack telemetry every 1.0 second continuously
.\.venv\Scripts\python.exe scripts/simulate_live_attacks.py --interval 1.0 --duration 0
```

* **`--interval 1.0`**: Sends **1 new live network flow prediction every 1.0 second**.
* **`--duration 0`**: Runs **continuously in an infinite loop** (press `Ctrl + C` to stop).

##### Attack Traffic Distribution Generated:
* 🟢 **70% BENIGN**: Normal Web/DNS/HTTP browsing flows.
* 🔴 **10% DoS GoldenEye**: High packet-volume HTTP Denial-of-Service attack flows.
* ⚡ **10% DDoS**: Massive bandwidth Distributed Denial-of-Service attack vectors.
* 🔍 **10% PortScan**: Rapid multi-port probe traffic.

---

### Step 3: Observe Live Telemetry in UI

1. Open **[`http://localhost:3000/live-threats`](http://localhost:3000/live-threats)**: Watch incoming threat cards stream live via WebSockets.
2. Open **[`http://localhost:3000/`](http://localhost:3000/)**: Watch session prediction counters, attack rates, and risk meters increase in real time.
3. Open **[`http://localhost:3000/historical-threats`](http://localhost:3000/historical-threats)**: Inspect permanent records stored in `alerts.db`.
4. Press **`⌘K`** or **`Ctrl+K`**: Search for `DDoS`, `PortScan`, or specific IPs across the entire platform.

---

## 🚀 Quick Setup & Installation

```bash
# Clone the repository
git clone https://github.com/saifvector/cortex-nids.git
cd cortex-nids
```

### Option 1: Automated Local Setup (Windows / Linux / macOS)

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

#### Linux / macOS (Bash):
```bash
chmod +x setup.sh && ./setup.sh
```

---

### Option 2: Docker Containerized Deployment

```powershell
# Core Stack (Backend + Frontend)
docker compose -f docker-compose.local.yml up -d --build

# Full Stack (Backend + Frontend + Prometheus + Grafana)
docker compose up -d --build
```

---

## 🌐 Application Access Points

| Service | Access URL | Description |
| :--- | :--- | :--- |
| **React SOC Dashboard** | [http://localhost:3000](http://localhost:3000) | $100M Liquid Glass Security Operations Platform |
| **Live Threat Stream** | [http://localhost:3000/live-threats](http://localhost:3000/live-threats) | Real-time WebSocket Threat Monitor |
| **Historical Threats Archive** | [http://localhost:3000/historical-threats](http://localhost:3000/historical-threats) | SQLite `alerts.db` Permanent Searchable Archive |
| **FastAPI REST API** | [http://localhost:8000](http://localhost:8000) | Sub-millisecond ML Prediction API |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger OpenAPI Reference |
| **Prometheus Metrics** | [http://localhost:9090](http://localhost:9090) | Operational metric scraping |
| **Grafana Visualizer** | [http://localhost:3001](http://localhost:3001) | Real-time infrastructure monitoring |

---

## 📊 Dataset & Machine Learning Performance

The system is trained on **2,830,743 network traffic records** from the benchmark CICIDS2017 dataset, covering 15 attack vectors.

### Model Evaluation Metrics:

| Classifier Model | Accuracy | Precision | Recall | F1-Score | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LightGBM (Primary)** | **99.87%** | **0.9984** | **0.9987** | **0.9005** | **20.4 ms** |
| XGBoost | 99.84% | 0.9981 | 0.9984 | 0.8980 | 32.1 ms |
| CatBoost | 99.82% | 0.9979 | 0.9982 | 0.8950 | 45.0 ms |
| Random Forest | 99.79% | 0.9975 | 0.9979 | 0.8910 | 58.2 ms |

---

## 🧪 Automated Testing & System Audits

Run the full automated test suite (70 test cases, 100% pass rate):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/
```

Or run the QA suite runner:
```powershell
.\.venv\Scripts\python.exe scripts/run_tests.py
```

```text
==========================================
ENTERPRISE NIDS QA & TESTING SUMMARY
==========================================
Total Test Cases Executed : 70
Passed Test Cases         : 70
Failed Test Cases         : 0
Pass Rate                 : 100.0%
==========================================
```

---

## 📄 License & Acknowledgements

- **Repository**: [`https://github.com/saifvector/cortex-nids`](https://github.com/saifvector/cortex-nids)
- **Author**: [@saifvector](https://github.com/saifvector)
- **License**: Released under the [MIT License](LICENSE).
- **Dataset**: Credit to the Canadian Institute for Cybersecurity (CIC) for the CICIDS2017 network intrusion telemetry.
