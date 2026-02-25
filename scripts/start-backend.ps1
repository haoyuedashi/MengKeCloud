param(
    [int]$Port = 8001,
    [string]$BindHost = "127.0.0.1",
    [int]$TimeoutSeconds = 45,
    [string]$AuthEnabled = "true",
    [switch]$ForceRestart
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$healthUrl = "http://$BindHost`:$Port/health"

function Test-PortListening {
    param([int]$CheckPort)

    $netstat = netstat -ano | Select-String ":$CheckPort"
    if (-not $netstat) {
        return $false
    }

    foreach ($line in $netstat) {
        if ($line.Line -match "LISTENING") {
            return $true
        }
    }

    return $false
}

if (Test-PortListening -CheckPort $Port) {
    if (-not $ForceRestart) {
        Write-Host "Backend already listening on $BindHost`:$Port"
        exit 0
    }

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($ownerPid in $listeners) {
        try {
            Stop-Process -Id $ownerPid -Force -ErrorAction Stop
        }
        catch {
            # ignore stale pid / race conditions
        }
    }
    Start-Sleep -Milliseconds 800
}

$args = @("-m", "uvicorn", "main:app", "--host", $BindHost, "--port", "$Port", "--reload")
$rawAuthEnabled = if ([string]::IsNullOrWhiteSpace($AuthEnabled)) { "true" } else { $AuthEnabled }
$authEnabledNormalized = $rawAuthEnabled.ToLowerInvariant()
$authEnabled = $authEnabledNormalized -in @("true", "1", "yes", "y")
$env:MENGKE_AUTH_ENABLED = if ($authEnabled) { "true" } else { "false" }
Start-Process python -ArgumentList $args -WorkingDirectory $repoRoot | Out-Null

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            Write-Host "Backend started: $healthUrl"
            exit 0
        }
    }
    catch {
        # wait until ready
    }
}

Write-Error "Backend did not become ready within $TimeoutSeconds seconds."
exit 1
