<#
.SYNOPSIS
    Start the full Iceberg Lakehouse stack including Streamlit dashboard and Airflow.

.DESCRIPTION
    Starts all Docker services:
      - MinIO        (S3-compatible object store)
      - Nessie       (Iceberg catalog)
      - Spark        (data processing engine)
      - Trino        (SQL query engine)
      - Streamlit    (analytics dashboard)   port 8501
      - Airflow      (pipeline orchestration) port 8082
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "  Iceberg Lakehouse - Full Stack Startup" -ForegroundColor Cyan
Write-Host "  =======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $Root

Write-Host "  Building and starting Docker services..." -ForegroundColor Yellow
docker compose -f docker/docker-compose.yml up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: docker compose up failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Waiting 30s for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "  Stack is running!" -ForegroundColor Green
Write-Host ""
Write-Host "  Service URLs:" -ForegroundColor White
Write-Host "    MinIO Console  : http://localhost:9001" -ForegroundColor Gray
Write-Host "    Nessie API     : http://localhost:19120" -ForegroundColor Gray
Write-Host "    Trino UI       : http://localhost:8080" -ForegroundColor Gray
Write-Host "    Spark UI       : http://localhost:4040" -ForegroundColor Gray
Write-Host "    Dashboard      : http://localhost:8501" -ForegroundColor Green
Write-Host "    Airflow        : http://localhost:8082  (admin / admin)" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Run the pipeline   : .\scripts\run_pipeline.ps1" -ForegroundColor Gray
Write-Host "    2. View dashboard     : http://localhost:8501" -ForegroundColor Gray
Write-Host "    3. Trigger DAG        : http://localhost:8082" -ForegroundColor Gray
Write-Host "    4. Run dbt models     : .\scripts\run_dbt.ps1" -ForegroundColor Gray
Write-Host ""
