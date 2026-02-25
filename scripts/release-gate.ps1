param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Running backend tests..."
pytest -q

if (-not $SkipBuild) {
    Write-Host "[2/3] Building frontend..."
    npm run build
} else {
    Write-Host "[2/3] Frontend build skipped by parameter"
}

Write-Host "[3/3] Release gate passed. Ready for first release."
