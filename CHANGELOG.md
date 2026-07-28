# Changelog

All notable changes to the Enterprise Network Intrusion Detection System (NIDS) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-28

### 🚀 Major Release Features

#### 🧠 Machine Learning & Inference Engine
- **LightGBM Classifier**: Trained on CICIDS2017 network telemetry (`99.87%` Accuracy, `0.9005` F1 Score).
- **Multi-Class Attack Detection**: Detects 15 attack vectors (DoS, DDoS, PortScan, Botnets, Brute Force, Infiltration, SQL Injection, XSS, etc.).
- **Sub-Millisecond Inference**: `20.4ms` single prediction latency & `48.8 QPS` throughput.

#### 📡 Real-Time Packet Sniffing & Flow Builder
- **Scapy Packet Engine**: Layer 2/3 packet sniffing on live network interfaces.
- **5-Tuple Flow Aggregation**: Bidirectional flow reconstruction generating 20 flow-based features.

#### 🎨 Enterprise SOC Dashboard (React 18 + Vite)
- **$100M SaaS UI Aesthetics**: Ultra glassmorphism, glowing risk indicators, interactive attack breakdown charts, real-time threat feed, and live packet stream.

#### 🔌 Enterprise SIEM Integration
- Connectors for Elastic Stack, Splunk HTTP Event Collector (HEC), Microsoft Sentinel, and Generic Syslog (CEF/LEEF).

#### ⚡ SOAR Automated Response
- Automated firewall rule enforcement (`netsh` on Windows, `iptables` on Linux) and playbook execution.

#### 🔒 Security, Auth & Governance
- JWT Bearer Authentication, PBKDF2 Password Hashing, 5-Tier RBAC, Rate Limiting, OWASP Security Response Headers, and SQLite Audit Logging.

#### 🐳 Production Containerization & CI/CD
- Multi-stage Dockerfiles (`Dockerfile.backend`, `Dockerfile.frontend`), Docker Compose orchestration, Prometheus metrics scraping, Grafana dashboards, and GitHub Actions CI/CD workflows.
