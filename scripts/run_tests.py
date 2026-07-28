"""
Automated Pytest Test Suite Runner & QA Report Generator for NIDS.
Runs all tests across API, Auth, ML, Packet Capture, Security, and Docker specifications.
Generates reports in reports/testing/test_report.md and reports/testing/test_report.html.
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.utils import ensure_directory, get_absolute_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_tests")


class QACollector:
    """Collects pytest execution statistics."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.total += 1
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1
            elif report.skipped:
                self.skipped += 1


def main():
    logger.info("Starting Enterprise NIDS Automated QA & Testing Suite...")

    report_dir = ensure_directory(get_absolute_path("reports/testing"))
    md_path = report_dir / "test_report.md"
    html_path = report_dir / "test_report.html"

    collector = QACollector()
    t0 = time.time()

    # Run Pytest programmatically
    args = [
        str(get_absolute_path("tests")),
        "-v",
        "--tb=short"
    ]

    exit_code = pytest.main(args, plugins=[collector])
    elapsed_sec = time.time() - t0

    pass_rate = (collector.passed / collector.total * 100.0) if collector.total > 0 else 100.0

    # Write Markdown Test Report
    md_report = f"""# Enterprise NIDS Automated Testing & QA Report

**Execution Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Duration**: {elapsed_sec:.2f} seconds  
**Test Suite Result**: {"✅ ALL TESTS PASSED" if collector.failed == 0 else "❌ TESTS FAILED"}

---

## 📊 Test Execution Statistics

| Metric | Result |
| :--- | :--- |
| **Total Test Cases** | `{collector.total}` |
| **Passed Test Cases** | `{collector.passed}` |
| **Failed Test Cases** | `{collector.failed}` |
| **Skipped Test Cases** | `{collector.skipped}` |
| **Pass Rate** | `{pass_rate:.1f}%` |

---

## 🛡️ Test Categories Covered

1. **FastAPI Endpoints**: `/predict`, `/batch_predict`, `/health`, `/metrics`, `/alerts`, `/threats`, `/ioc`, `/siem/status`, `/mitigation/rules`
2. **Authentication & JWT**: PBKDF2 Hashing, Access Tokens, Refresh Tokens, User Account Lifecycle
3. **Machine Learning Pipeline**: Model Loading, Feature Alignment, Scaler Pipeline, Class Probabilities
4. **Prediction Engine**: Risk Score (0-100) Calculation, Confidence Scoring, Risk Level Categories
5. **Packet Sniffing & Flow Builder**: 5-Tuple Aggregation, 20-Feature Extraction, SQLite Stored Alert Querying
6. **Security & RBAC**: HTTP Security Response Headers, Token-Bucket Rate Limiter, 5-Tier RBAC Permission Matrix
7. **Docker & Specifications**: `Dockerfile.backend`, `Dockerfile.frontend`, and `docker-compose.local.yml` Validation
"""
    md_path.write_text(md_report, encoding="utf-8")

    # Write HTML Test Report
    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NIDS Automated QA Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 2rem; max-width: 800px; margin: 0 auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }}
        h1 {{ color: #38bdf8; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; }}
        .pass {{ color: #4ade80; font-weight: bold; }}
        .fail {{ color: #f87171; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🛡️ NIDS QA & Test Execution Report</h1>
        <p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Status:</strong> <span class="{"pass" if collector.failed == 0 else "fail"}">{"ALL PASSED" if collector.failed == 0 else "FAILED"}</span></p>

        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Tests</td><td>{collector.total}</td></tr>
            <tr><td>Passed Tests</td><td class="pass">{collector.passed}</td></tr>
            <tr><td>Failed Tests</td><td class="fail">{collector.failed}</td></tr>
            <tr><td>Pass Rate</td><td>{pass_rate:.1f}%</td></tr>
            <tr><td>Duration</td><td>{elapsed_sec:.2f}s</td></tr>
        </table>
    </div>
</body>
</html>
"""
    html_path.write_text(html_report, encoding="utf-8")

    print("\n==========================================")
    print("ENTERPRISE NIDS QA & TESTING SUMMARY")
    print("==========================================")
    print(f"Total Test Cases Executed : {collector.total}")
    print(f"Passed Test Cases         : {collector.passed}")
    print(f"Failed Test Cases         : {collector.failed}")
    print(f"Pass Rate                 : {pass_rate:.1f}%")
    print(f"Test Reports Generated    : {md_path}")
    print("==========================================\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
