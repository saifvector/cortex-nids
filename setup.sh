#!/usr/bin/env bash
# Universal Linux / macOS Automated Setup & Installation Script for Enterprise NIDS
set -e

echo "=================================================="
echo " CORTEX NIDS - AUTOMATED LINUX/MAC SETUP ENGINE"
echo "=================================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Verify Python 3.11+ Toolchain
echo ""
echo "[1/7] Verifying Python 3.11+ Toolchain..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MAJOR" -eq 3 -a "$PY_MINOR" -lt 11 ]; then
    echo "Error: Python version $PY_VER is unsupported. Enterprise NIDS requires Python 3.11+."
    exit 1
fi
echo "  Found Python $PY_VER (OK)"

# 2. Check Git, Node.js, and npm
echo ""
echo "[2/7] Checking Git, Node.js, and npm..."
for tool in git node npm; do
    if ! command -v $tool &> /dev/null; then
        echo "Error: Required tool '$tool' is not installed or not available in PATH."
        exit 1
    fi
    echo "  Found $tool (OK)"
done

# 3. Create Project Directory Structure
echo ""
echo "[3/7] Creating required storage directories..."
folders=("reports" "predictions" "logs" "temp" "uploads" "data/raw" "data/processed" "models/optimized")
for folder in "${folders[@]}"; do
    if [ ! -d "$folder" ]; then
        mkdir -p "$folder"
        echo "  Created directory: $folder"
    fi
done
echo "  Directories verified (OK)"

# 4. Copy .env.example to .env if missing
echo ""
echo "[4/7] Verifying environment configuration (.env)..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  Copied .env.example to .env (OK)"
    fi
else
    echo "  Existing .env configuration found (OK)"
fi

# 5. Setup Python Virtual Environment & Install Dependencies
echo ""
echo "[5/7] Setting up Python Virtual Environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  Created Python virtual environment at .venv"
fi

source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -r requirements-dev.txt --quiet
echo "  Python dependencies installed successfully (OK)"

# 6. Install Frontend Dependencies
echo ""
echo "[6/7] Installing Frontend React dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install --quiet
    cd "$PROJECT_ROOT"
    echo "  Frontend npm dependencies installed (OK)"
fi

# 7. Run Environment Validation Engine
echo ""
echo "[7/7] Executing Comprehensive Environment Validation Check..."
python3 scripts/check_environment.py

echo ""
echo "=================================================="
echo " LOCAL SETUP COMPLETE! HOW TO RUN THE PLATFORM:"
echo "=================================================="
echo " 1. Run FastAPI Backend Server:"
echo "    .venv/bin/python scripts/run_api.py"
echo ""
echo " 2. Run React SOC Dashboard:"
echo "    cd frontend && npm run dev"
echo "=================================================="
