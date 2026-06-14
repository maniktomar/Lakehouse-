<#
.SYNOPSIS
    Run dbt models and tests against the Trino / Iceberg lakehouse.

.DESCRIPTION
    Executes:
      dbt run   - creates/refreshes staging views + mart tables in Trino
      dbt test  - validates column-level data quality rules

    Prerequisites:
      - Trino must be running at localhost:8080 (run start.ps1 or start_full.ps1 first)
      - dbt-trino must be installed (pip install dbt-trino==1.8.4)

    Models created:
      lakehouse.silver.stg_orders            (view)
      lakehouse.gold.daily_sales             (table)
      lakehouse.gold.channel_performance     (table)
      lakehouse.gold.category_performance    (table)
#>

$ErrorActionPreference = "Stop"
$Root    = Split-Path -Parent $PSScriptRoot
$DbtDir  = Join-Path $Root "dbt"

Write-Host ""
Write-Host "  Running dbt models against Trino/Iceberg" -ForegroundColor Cyan
Write-Host "  =========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $DbtDir

# Activate the project virtualenv if present
$VenvActivate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    . $VenvActivate
}

# Check dbt is available
if (-not (Get-Command dbt -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: dbt not found. Install it:" -ForegroundColor Red
    Write-Host "      pip install dbt-trino==1.8.4" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Running dbt run (creates and refreshes all models)..." -ForegroundColor Yellow
dbt run --profiles-dir .

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: dbt run failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Running dbt test (validates data quality rules)..." -ForegroundColor Yellow
dbt test --profiles-dir .

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: dbt test failed. Check output above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  SUCCESS: All dbt models built and tests passed!" -ForegroundColor Green
Write-Host ""
Write-Host "  Models available in Trino:" -ForegroundColor White
Write-Host "    SELECT * FROM lakehouse.silver.stg_orders LIMIT 10;" -ForegroundColor Gray
Write-Host "    SELECT * FROM lakehouse.gold.daily_sales LIMIT 10;" -ForegroundColor Gray
Write-Host "    SELECT * FROM lakehouse.gold.channel_performance;" -ForegroundColor Gray
Write-Host "    SELECT * FROM lakehouse.gold.category_performance;" -ForegroundColor Gray
Write-Host ""
