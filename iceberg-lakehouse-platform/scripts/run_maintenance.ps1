Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\spark-submit.ps1" -Job "src/maintenance.py"
