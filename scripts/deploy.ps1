# Enterprise NIDS Production Deployment Automation Script (PowerShell)
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CORTEX NIDS PRODUCTION DEPLOYMENT ENGINE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Docker availability
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not available in PATH."
    exit 1
}

Write-Host "[1/3] Building production container images..." -ForegroundColor Yellow
docker compose build

Write-Host "[2/3] Starting container orchestration stack..." -ForegroundColor Yellow
docker compose up -d

Write-Host "[3/3] Verifying container health..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
docker compose ps

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "React SOC Dashboard: http://localhost:3000" -ForegroundColor Green
Write-Host "FastAPI REST Server:  http://localhost:8000" -ForegroundColor Green
Write-Host "Prometheus Metrics:   http://localhost:9090" -ForegroundColor Green
Write-Host "Grafana Dashboard:    http://localhost:3001" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
