param(
    [int]$Port = 8001,
    [string]$BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

Write-Host "[Staging Rehearsal] Start backend with auth enabled"
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/start-backend.ps1" -Port $Port -BindHost $BindHost -AuthEnabled 1

Write-Host "[Staging Rehearsal] Check backend health"
$health = Invoke-WebRequest -UseBasicParsing "http://$BindHost`:$Port/health" -TimeoutSec 5
if ($health.StatusCode -ne 200) {
    throw "health check failed"
}

Write-Host "[Staging Rehearsal] Run release gate"
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/release-gate.ps1"

Write-Host "[Staging Rehearsal] PASSED"
