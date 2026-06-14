param(
    [Parameter(Mandatory = $true)]
    [string]$Job,

    [string[]]$JobArguments = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Packages = @(
    "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.8.1"
    "org.apache.iceberg:iceberg-aws-bundle:1.8.1"
    "org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.102.5"
) -join ","

docker compose -f docker/docker-compose.yml exec spark `
    /opt/spark/bin/spark-submit `
    --conf "spark.jars.ivy=/tmp/iceberg-ivy" `
    --conf "spark.driver.extraJavaOptions=-Dpython.path=/opt/lakehouse" `
    --conf "spark.executorEnv.PYTHONPATH=/opt/lakehouse" `
    --conf "spark.yarn.appMasterEnv.PYTHONPATH=/opt/lakehouse" `
    --packages $Packages $Job @JobArguments

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
