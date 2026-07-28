"""
Environment and Dependency Validation Engine for NIDS.
Verifies system requirements, toolchain versions, dataset/model presence, and port availability.
"""
import os
import sys
import shutil
import socket
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def check_python_version() -> Tuple[bool, str]:
    version = sys.version_info
    v_str = f"{version.major}.{version.minor}.{version.micro}"
    if version.major == 3 and version.minor >= 11:
        return True, f"Python {v_str} (Supported)"
    return False, f"Python {v_str} (Requires 3.11+)"


def check_tool(tool_name: str) -> Tuple[bool, str]:
    path = shutil.which(tool_name)
    if not path:
        return False, f"{tool_name} not found in PATH"
    try:
        out = subprocess.check_output([tool_name, "--version"], stderr=subprocess.STDOUT, text=True).strip()
        first_line = out.split("\n")[0]
        return True, f"{tool_name}: {first_line}"
    except Exception:
        return True, f"{tool_name} installed at {path}"


def check_ram() -> Tuple[bool, str]:
    total_gb = psutil.virtual_memory().total / (1024 ** 3)
    if total_gb >= 4.0:
        return True, f"{total_gb:.1f} GB RAM available"
    return False, f"{total_gb:.1f} GB RAM (4.0 GB recommended)"


def check_disk_space() -> Tuple[bool, str]:
    free_gb = shutil.disk_usage(PROJECT_ROOT).free / (1024 ** 3)
    if free_gb >= 2.0:
        return True, f"{free_gb:.1f} GB free disk space"
    return False, f"{free_gb:.1f} GB free disk space (2.0 GB required)"


def check_port(port: int, name: str) -> Tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    if result != 0:
        return True, f"Port {port} ({name}) is Available"
    return False, f"Port {port} ({name}) is currently IN USE"


def check_file(rel_paths: List[str], label: str) -> Tuple[bool, str]:
    for rel_path in rel_paths:
        p = PROJECT_ROOT / rel_path
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024) if p.is_file() else 0
            return True, f"{label} present at {rel_path} ({size_mb:.1f} MB)"
    return False, f"{label} missing at {', '.join(rel_paths)}"


def check_dir(rel_path: str, label: str) -> Tuple[bool, str]:
    p = PROJECT_ROOT / rel_path
    if p.exists():
        return True, f"{label} present at {rel_path}"
    return False, f"{label} missing at {rel_path}"


def main() -> int:
    print(f"\n{CYAN}==================================================")
    print("NIDS UNIVERSAL ENVIRONMENT & DEPENDENCY VALIDATOR")
    print(f"=================================================={RESET}\n")

    checks: List[Tuple[str, bool, str]] = []

    # 1. Python & Tools
    py_ok, py_msg = check_python_version()
    checks.append(("Python 3.11+", py_ok, py_msg))

    git_ok, git_msg = check_tool("git")
    checks.append(("Git CLI", git_ok, git_msg))

    node_ok, node_msg = check_tool("node")
    checks.append(("Node.js", node_ok, node_msg))

    npm_ok, npm_msg = check_tool("npm")
    checks.append(("npm Package Manager", npm_ok, npm_msg))

    # 2. System Hardware
    ram_ok, ram_msg = check_ram()
    checks.append(("System Memory", ram_ok, ram_msg))

    disk_ok, disk_msg = check_disk_space()
    checks.append(("Free Disk Space", disk_ok, disk_msg))

    # 3. Ports
    for port, service in [(8000, "FastAPI Backend"), (3000, "React Dashboard"), (9090, "Prometheus"), (3001, "Grafana")]:
        p_ok, p_msg = check_port(port, service)
        checks.append((f"Port {port}", p_ok, p_msg))

    # 4. Data & Models
    model_ok, model_msg = check_file(["models/best_model.joblib", "models/optimized/best_model.joblib"], "Trained ML Model")
    checks.append(("ML Model Artifact", model_ok, model_msg))

    pipe_ok, pipe_msg = check_file(["data/processed/preprocessing_pipeline.joblib", "models/preprocessing_pipeline.joblib", "models/optimized/preprocessing_pipeline.joblib"], "Preprocessing Pipeline")
    checks.append(("ML Pipeline Artifact", pipe_ok, pipe_msg))

    data_ok, data_msg = check_file(["data/processed/processed_data.csv", "data/raw/network_traffic.csv"], "Dataset File")
    if not data_ok:
        data_ok, data_msg = check_dir("data/raw", "Raw Dataset Directory")
    checks.append(("Dataset Availability", data_ok, data_msg))

    # 5. Frontend & Structure
    node_mod_ok, node_mod_msg = check_dir("frontend/node_modules", "Frontend Dependencies")
    checks.append(("Frontend node_modules", node_mod_ok, node_mod_msg))

    # Print Table
    failed_count = 0
    for name, status, details in checks:
        if status:
            tag = f"[{GREEN}PASS{RESET}]"
        else:
            tag = f"[{RED}FAIL{RESET}]"
            failed_count += 1
        print(f" {tag} {name:<24}: {details}")

    print(f"\n{CYAN}==================================================")
    if failed_count == 0:
        print(f"{GREEN}ALL ENVIRONMENT CHECKS PASSED! Platform is ready for local execution.{RESET}")
    else:
        print(f"{YELLOW}FOUND {failed_count} WARNING(S) / ISSUES. Review details above.{RESET}")
    print(f"=================================================={RESET}\n")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
