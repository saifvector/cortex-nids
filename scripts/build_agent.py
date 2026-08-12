#!/usr/bin/env python
"""
Automated PyInstaller build script for CortexAgent.exe.
Packages agent/main.py, LightGBM model artifacts, and preprocessors into a standalone Windows executable.
"""
import sys
import subprocess
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def build_cortex_agent():
    logging.info("Starting PyInstaller packaging for CortexAgent.exe...")

    # Ensure pyinstaller is installed in .venv
    pyinstaller_bin = PROJECT_ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_bin.exists():
        pyinstaller_bin = "pyinstaller"

    icon_path = PROJECT_ROOT / "agent" / "assets" / "cortex_icon.ico"

    cmd = [
        str(pyinstaller_bin),
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "CortexAgent",
        "--icon", str(icon_path) if icon_path.exists() else "",
        "--collect-all", "customtkinter",
        "--collect-all", "lightgbm",
        "--collect-all", "psutil",
        "--collect-all", "src",
        "--hidden-import", "psutil",
        "--hidden-import", "src",
        "--hidden-import", "src.encoding",
        "--hidden-import", "src.preprocessing",
        "--hidden-import", "src.scaling",
        "--hidden-import", "src.feature_selection",
        "--hidden-import", "src.data_loader",
        "--hidden-import", "src.data_validator",
        "--hidden-import", "src.evaluator",
        "--hidden-import", "src.predictor",
        "--hidden-import", "src.model_loader",
        "--hidden-import", "src.inference_pipeline",
        "--hidden-import", "src.prediction_service",
        "--hidden-import", "src.alert_engine",
        "--hidden-import", "src.packet_capture",
        "--hidden-import", "src.flow_builder",
        "--hidden-import", "src.exceptions.custom_exceptions",
        "--hidden-import", "sklearn",
        "--hidden-import", "sklearn.ensemble",
        "--hidden-import", "sklearn.preprocessing",
        "--hidden-import", "joblib",
        "--add-data", f"{PROJECT_ROOT / 'models' / 'best_model.joblib'};models",
        "--add-data", f"{PROJECT_ROOT / 'models' / 'metadata.json'};models",
        "--add-data", f"{PROJECT_ROOT / 'data' / 'processed' / 'feature_names.json'};data/processed",
        "--add-data", f"{PROJECT_ROOT / 'data' / 'processed' / 'preprocessing_pipeline.joblib'};data/processed",
        "--add-data", f"{PROJECT_ROOT / 'agent' / 'assets'};agent/assets",
        str(PROJECT_ROOT / "agent" / "main.py")
    ]

    # Remove empty --icon argument if icon doesn't exist
    if not icon_path.exists():
        cmd = [c for c in cmd if c != "--icon" and c != ""]

    logging.info("Executing PyInstaller build command:")
    logging.info(" ".join(cmd))

    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode == 0:
        exe_path = PROJECT_ROOT / "dist" / "CortexAgent.exe"
        logging.info("=" * 60)
        logging.info("SUCCESS: Standalone CortexAgent.exe packaged successfully!")
        logging.info("Executable Path: %s", exe_path)
        logging.info("File Size: %.2f MB", exe_path.stat().st_size / (1024 * 1024))
        logging.info("=" * 60)
    else:
        logging.error("PyInstaller build failed with exit code %d", res.returncode)
        sys.exit(res.returncode)


if __name__ == "__main__":
    build_cortex_agent()
