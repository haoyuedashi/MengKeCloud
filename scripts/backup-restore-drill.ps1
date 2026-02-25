param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$dbName = $env:MENGKE_DB_NAME
$dbUser = $env:MENGKE_DB_USER
$dbHost = $env:MENGKE_DB_HOST
$dbPort = $env:MENGKE_DB_PORT
$backupFile = Join-Path $PSScriptRoot "..\tmp\mengkecloud-backup.sql"

if (-not $dbName) { $dbName = "mengkecloud" }
if (-not $dbUser) { $dbUser = "postgres" }
if (-not $dbHost) { $dbHost = "127.0.0.1" }
if (-not $dbPort) { $dbPort = "5432" }

Write-Host "[Backup/Restore Drill] Target: $dbUser@${dbHost}:${dbPort}/$dbName"

if ($DryRun) {
    Write-Host "DryRun=true, planned commands:"
    Write-Host "  pg_dump -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $backupFile"
    Write-Host "  psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $backupFile"
    Write-Host "[Backup/Restore Drill] DRY RUN PASSED"
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $backupFile -Parent) | Out-Null

Write-Host "[Backup/Restore Drill] Creating backup"
pg_dump -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $backupFile

Write-Host "[Backup/Restore Drill] Restoring backup"
psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $backupFile

Write-Host "[Backup/Restore Drill] PASSED"
