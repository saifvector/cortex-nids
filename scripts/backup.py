"""
Automated Backup & Disaster Recovery Management Engine for NIDS.
Creates compressed timestamped backups of models, predictions, reports, databases, and configs.
Supports restore functionality via --restore argument.
Generates reports/operations/backup_report.md.
"""
import argparse
import logging
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.utils import ensure_directory, get_absolute_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backup_engine")


def create_backup() -> Path:
    backup_dir = ensure_directory(get_absolute_path("backups"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = backup_dir / f"nids_backup_{timestamp}.zip"

    target_dirs = ["models", "predictions", "reports", "config"]
    target_files = [".env", "VERSION"]

    logger.info("Creating compressed backup archive at: %s", zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for t_dir in target_dirs:
            dir_path = get_absolute_path(t_dir)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and ".git" not in file_path.parts:
                        arcname = file_path.relative_to(PROJECT_ROOT)
                        zipf.write(file_path, arcname=arcname)
                        logger.debug("Backed up: %s", arcname)

        for t_file in target_files:
            file_path = get_absolute_path(t_file)
            if file_path.exists():
                zipf.write(file_path, arcname=t_file)
                logger.debug("Backed up file: %s", t_file)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    logger.info("Backup created successfully! Archive size: %.2f MB", size_mb)

    # Generate Backup Report
    report_dir = ensure_directory(get_absolute_path("reports/operations"))
    report_path = report_dir / "backup_report.md"

    report_md = f"""# Automated Backup & Recovery Report

**Backup Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Archive Location**: `{zip_path}`  
**Archive Size**: `{size_mb:.2f} MB`  
**Status**: 🟢 SUCCESSFUL

---

## 📦 Backed Up Directories & Assets

- `models/`: Trained LightGBM model binaries and scalers
- `predictions/`: SQLite alert database (`alerts.db`), CSV/JSON prediction logs
- `reports/`: Audit, EDA, evaluation, explainability, testing, and operations reports
- `config/`: System YAML configuration and logging settings
- `.env` & `VERSION`: Environment secrets and version metadata

---

## 🔄 Disaster Recovery Procedure

To restore from this backup archive:

```bash
python scripts/backup.py --restore "{zip_path}"
```
"""
    report_path.write_text(report_md, encoding="utf-8")
    return zip_path


def restore_backup(zip_path_str: str) -> None:
    zip_path = Path(zip_path_str)
    if not zip_path.exists():
        logger.error("Backup file not found: %s", zip_path)
        sys.exit(1)

    logger.info("Restoring project state from backup: %s", zip_path)
    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(PROJECT_ROOT)

    logger.info("Restore operation completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="NIDS Backup & Disaster Recovery Tool")
    parser.add_argument("--restore", type=str, help="Path to backup zip file to restore")
    args = parser.parse_args()

    if args.restore:
        restore_backup(args.restore)
    else:
        zip_path = create_backup()
        print("\n==========================================")
        print("BACKUP OPERATION COMPLETE")
        print("==========================================")
        print(f"Archive Created : {zip_path}")
        print(f"Archive Size    : {zip_path.stat().st_size / (1024*1024):.2f} MB")
        print("==========================================\n")


if __name__ == "__main__":
    main()
