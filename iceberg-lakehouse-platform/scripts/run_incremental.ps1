Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m src.generate_changes --count 250
& "$PSScriptRoot\spark-submit.ps1" -Job "src/incremental_upsert.py"
& "$PSScriptRoot\spark-submit.ps1" -Job "src/pipeline_audit.py"
