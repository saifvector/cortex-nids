#!/bin/bash
# Unix/macOS runner script for NIDS pipeline
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "[ERROR] Virtual environment (.venv) not found."
    echo "Please setup a virtual environment and install requirements first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Run the pipeline with all forwarded arguments
python scripts/run_pipeline.py "$@"

# Deactivate
deactivate
