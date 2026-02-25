param(
    [int]$Port = 8001,
    [string]$BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$baseUrl = "http://$BindHost`:$Port"
$healthUrl = "$baseUrl/health"

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

$listening = Test-PortListening -CheckPort $Port
Write-Host "Port listening ($Port): $listening"

try {
    $rootResp = Invoke-WebRequest -UseBasicParsing "$baseUrl/" -TimeoutSec 3
    Write-Host "Root status: $($rootResp.StatusCode)"
}
catch {
    Write-Host "Root status: unreachable"
}

try {
    $healthResp = Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 3
    Write-Host "Health status: $($healthResp.StatusCode)"
}
catch {
    Write-Host "Health status: unreachable"
}

if (-not $listening) {
    exit 1
}
