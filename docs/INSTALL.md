# Installation & Setup Guide

Comprehensive setup instructions for deploying the Enterprise Network Intrusion Detection System locally or via Docker.

---

## 📋 System Requirements

### Hardware Requirements:
- **CPU**: Dual-core 2.0 GHz or higher (Quad-core recommended).
- **RAM**: Minimum 4.0 GB (8.0 GB recommended).
- **Disk Space**: Minimum 2.0 GB free disk space.

### Software Prerequisites:
- **Python**: Version 3.11+
- **Node.js**: Version 20+ & `npm`
- **Git**: Installed and in system PATH
- **Docker & Docker Desktop** *(Optional for containerized deployment)*

---

## 🚀 Option 1: Automated Local Installation (Recommended)

### Windows (PowerShell):
```powershell
# Run automated setup
powershell -ExecutionPolicy Bypass -File setup.ps1

# Launch backend & frontend in parallel
powershell -ExecutionPolicy Bypass -File scripts\start_local.ps1
```

### Linux / macOS (Bash):
```bash
# Run automated setup
chmod +x setup.sh
./setup.sh

# Run FastAPI backend
.venv/bin/python scripts/run_api.py

# Run React frontend (in second terminal)
cd frontend && npm run dev
```

---

## 🐳 Option 2: Docker Containerized Deployment

### Launch Stack (Core Application):
```powershell
docker compose -f docker-compose.local.yml up -d --build
```

### Launch Full Enterprise Stack (Backend + Frontend + Prometheus + Grafana):
```powershell
docker compose up -d --build
```

### Check Container Health:
```powershell
docker compose ps
```

---

## 🔍 Verifying Installation

Run the system environment validator:

```bash
python scripts/check_environment.py
```
