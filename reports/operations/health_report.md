# SRE System Health & Observability Report

**Generated Timestamp**: 2026-07-28 12:29:22  
**Overall System Health**: 🟢 ALL SYSTEMS OPERATIONAL

---

## 📊 Health Check Breakdown

| Component | Status | Operational Details |
| :--- | :---: | :--- |
| **CPU Utilization** | 🟢 PASS | `13.4% used` |
| **System Memory** | 🟢 PASS | `76.5% used (11.7/15.3 GB)` |
| **Free Disk Space** | 🟢 PASS | `100.9 GB free` |
| **FastAPI Port 8000** | 🟢 PASS | `Port 8000 available` |
| **Frontend Port 3000** | 🟢 PASS | `Port 3000 available` |
| **Trained Model Binary** | 🟢 PASS | `Present at best_model.joblib (2.6 MB)` |
| **SQLite Alerts Database** | 🟢 PASS | `Present at alerts.db` |

---

## 🛠️ Observability Action Plan
- Ensure FastAPI Backend (`http://localhost:8000`) and SOC Dashboard (`http://localhost:3000`) are active.
- Verify log rotations under `logs/nids_app.log` and `logs/audit.log`.
