Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

docker compose -f docker/docker-compose.yml up -d --build
Write-Host "MinIO console: http://localhost:9001"
Write-Host "Nessie API: http://localhost:19120/api/v2/config"
Write-Host "Trino UI: http://localhost:8080"

