param(
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 5432,
    [string]$DbUser = "postgres",
    [string]$DbPassword = "postgres",
    [string]$DbName = "mengkecloud"
)

$ErrorActionPreference = "Stop"

$psqlPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (-not (Test-Path $psqlPath)) {
    Write-Error "psql not found at $psqlPath"
    exit 1
}

$sqlFile = Join-Path $PSScriptRoot "seed-demo-data.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Error "seed SQL file not found: $sqlFile"
    exit 1
}

$env:PGPASSWORD = $DbPassword

Write-Host "Seeding demo data into $DbName@$DbHost`:$DbPort ..."
& $psqlPath -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $sqlFile | Out-Host

Write-Host "Verifying counts..."
& $psqlPath -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT COUNT(*) AS users_count FROM users;" | Out-Host
& $psqlPath -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT COUNT(*) AS leads_count FROM leads;" | Out-Host
& $psqlPath -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT COUNT(*) AS followups_count FROM follow_up_records;" | Out-Host
& $psqlPath -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT COUNT(*) AS dict_items_count FROM dict_items;" | Out-Host

Write-Host "Seed completed."
