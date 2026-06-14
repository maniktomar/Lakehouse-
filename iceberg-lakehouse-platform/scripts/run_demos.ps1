Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

& "$PSScriptRoot\spark-submit.ps1" -Job "src/schema_evolution_demo.py"
& "$PSScriptRoot\spark-submit.ps1" -Job "src/time_travel_demo.py"
