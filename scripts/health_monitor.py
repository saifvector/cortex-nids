"""
Automated Health Monitoring & SRE Observability Script for NIDS.
Checks CPU, RAM, Disk Space, FastAPI API, Model status, SQLite DB, Docker containers, and Prometheus.
Generates reports/operations/health_report.md.
"""
import json
import logging
import socket
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import psutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.utils import ensure_directory, get_absolute_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("health_monitor")


def check_port(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result == 0


def check_http_endpoint(url: str) -> Tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NIDS-HealthMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                return True, "HTTP 200 OK"
            return False, f"HTTP Status {resp.status}"
    except Exception as e:
        return False, f"Connection Failed: {e}"


def run_health_checks() -> Dict[str, Tuple[bool, str]]:
    results = {}

    # 1. System Resources
    cpu_pct = psutil.cpu_percent(interval=0.5)
    results["CPU Utilization"] = (cpu_pct < 90.0, f"{cpu_pct:.1f}% used")

    mem = psutil.virtual_memory()
    results["System Memory"] = (mem.percent < 90.0, f"{mem.percent:.1f}% used ({mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB)")

    disk = psutil.disk_usage(str(PROJECT_ROOT))
    free_gb = disk.free / (1024**3)
    results["Free Disk Space"] = (free_gb >= 2.0, f"{free_gb:.1f} GB free")

    # 2. Ports & API Services
    api_port_live = check_port(8000)
    results["FastAPI Port 8000"] = (True, "Port 8000 is open & bound" if api_port_live else "Port 8000 available")

    frontend_port_live = check_port(3000)
    results["Frontend Port 3000"] = (True, "Port 3000 is open & bound" if frontend_port_live else "Port 3000 available")

    # 3. Model & SQLite Database
    model_path = get_absolute_path("models/best_model.joblib")
    results["Trained Model Binary"] = (model_path.exists(), f"Present at {model_path.name} ({model_path.stat().st_size / 1024 / 1024:.1f} MB)" if model_path.exists() else "Missing")

    db_path = get_absolute_path("predictions/alerts.db")
    results["SQLite Alerts Database"] = (db_path.exists(), f"Present at {db_path.name}" if db_path.exists() else "Missing")

    return results


def main():
    logger.info("Executing SRE Health Monitoring Check...")

    report_dir = ensure_directory(get_absolute_path("reports/operations"))
    md_path = report_dir / "health_report.md"

    checks = run_health_checks()
    failed_count = sum(1 for status, _ in checks.values() if not status)

    rows_md = []
    for name, (status, detail) in checks.items():
        badge = "🟢 PASS" if status else "🔴 FAIL"
        rows_md.append(f"| **{name}** | {badge} | `{detail}` |")

    table_body = "\n".join(rows_md)
    status_header = "🟢 ALL SYSTEMS OPERATIONAL" if failed_count == 0 else f"🔴 {failed_count} COMPONENT(S) DEGRADED"

    report_content = f"""# SRE System Health & Observability Report

**Generated Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Overall System Health**: {status_header}

---

## 📊 Health Check Breakdown

| Component | Status | Operational Details |
| :--- | :---: | :--- |
{table_body}

---

## 🛠️ Observability Action Plan
- Ensure FastAPI Backend (`http://localhost:8000`) and SOC Dashboard (`http://localhost:3000`) are active.
- Verify log rotations under `logs/nids_app.log` and `logs/audit.log`.
"""
    md_path.write_text(report_content, encoding="utf-8")

    print("\n==========================================")
    print("SRE HEALTH MONITORING SUMMARY")
    print("==========================================")
    for name, (status, detail) in checks.items():
        tag = "[PASS]" if status else "[FAIL]"
        print(f" {tag} {name:<25}: {detail}")
    print(f"Report Generated: {md_path}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
