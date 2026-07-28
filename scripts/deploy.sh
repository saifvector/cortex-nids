#!/usr/bin/env bash
# Enterprise NIDS Production Deployment Automation Script (Bash)
set -e

echo "=========================================="
echo "CORTEX NIDS PRODUCTION DEPLOYMENT ENGINE"
echo "=========================================="

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    exit 1
fi

echo "[1/3] Building production container images..."
docker compose build

echo "[2/3] Starting container orchestration stack..."
docker compose up -d

echo "[3/3] Verifying container health..."
sleep 5
docker compose ps

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "React SOC Dashboard: http://localhost:3000"
echo "FastAPI REST Server:  http://localhost:8000"
echo "Prometheus Metrics:   http://localhost:9090"
echo "Grafana Dashboard:    http://localhost:3001"
echo "=========================================="
