Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m src.generate_orders --count 5000
& "$PSScriptRoot\spark-submit.ps1" -Job "src/ingest_bronze.py"
& "$PSScriptRoot\spark-submit.ps1" -Job "src/build_silver_gold.py"
& "$PSScriptRoot\spark-submit.ps1" -Job "src/pipeline_audit.py"
