Push-Location $PSScriptRoot
$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$PID | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")

$LOG_FILE = "UpdateLog.txt"

. .\Common.ps1

Write-Log "Run heartbeat by user: $env:UserName"
# Run python Heartbeat
.\emar.exe --heartbeat
# TODO: Create process and wait for it to finish. put pid in heartbeat.pid file
# $proc = Start-Process -FilePath .\emar.exe --heartbeat
# $proc.Id | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")
# Wait-Process $proc

$PID | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")
Pop-Location
