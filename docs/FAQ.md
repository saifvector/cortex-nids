# Frequently Asked Questions (FAQ)

### Q1: What machine learning algorithms are supported by the platform?
**A**: The core engine uses an optimized **LightGBM Classifier** (`99.87%` accuracy). The pipeline also supports XGBoost, CatBoost, Extra Trees, Random Forest, Decision Trees, and Logistic Regression.

---

### Q2: Can the NIDS capture live network traffic?
**A**: Yes. Module 11 implements Scapy live packet capture on Windows (Npcap), Linux (`libpcap`), and macOS, converting raw 5-tuples into 20 flow-based features in real time.

---

### Q3: Does this require Docker to run?
**A**: No. While multi-stage Dockerfiles and Docker Compose files are included for cloud/Kubernetes deployment, the platform can be run locally using `setup.ps1` or `setup.sh`.

---

### Q4: How does the system handle class imbalance in network traffic?
**A**: The preprocessing pipeline (`src/preprocessing.py`) includes **SMOTE** (Synthetic Minority Over-sampling Technique) and **Random Under-Sampling (RUS)**, along with balanced class weighting.

---

### Q5: How do I export threat alerts to our company's SIEM?
**A**: Edit `.env` to enable Elastic, Splunk, Sentinel, or Syslog exporters and run `python scripts/run_siem.py`.
