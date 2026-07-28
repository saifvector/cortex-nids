# Troubleshooting & Common Issues Guide

Common issues and resolution steps for Enterprise NIDS.

---

## 🛠️ Common Errors & Solutions

### 1. `ModuleNotFoundError: No module named 'uvicorn'` (or other package)
- **Cause**: Script executed outside virtual environment.
- **Solution**:
  ```powershell
  .venv\Scripts\python.exe scripts\run_api.py
  ```

---

### 2. `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`
- **Cause**: Docker Desktop daemon is closed or initializing.
- **Solution**:
  1. Open **Docker Desktop**.
  2. Wait until status shows **`Engine running`** (green icon).
  3. Re-run `docker compose up -d`.

---

### 3. `RuntimeError: Form data requires "python-multipart" to be installed.`
- **Cause**: Missing `python-multipart` library.
- **Solution**:
  ```bash
  pip install python-multipart
  ```

---

### 4. `PermissionError: [WinError 5] Access is denied` during packet capture
- **Cause**: Scapy requires administrator privileges to access raw network sockets.
- **Solution**: Run PowerShell or CMD as **Administrator**.
