# Automated Backup & Recovery Report

**Backup Timestamp**: 2026-07-28 12:28:45  
**Archive Location**: `C:\Users\saifu\Desktop\Network Intrusion Detection\backups\nids_backup_20260728_122841.zip`  
**Archive Size**: `28.57 MB`  
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
python scripts/backup.py --restore "C:\Users\saifu\Desktop\Network Intrusion Detection\backups\nids_backup_20260728_122841.zip"
```
