Push-Location $PSScriptRoot
$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$PID | Out-File (Join-Path $cfg.backups_path "upgrade.pid")

$LOG_FILE = "UpdateLog.txt"

. .\Common.ps1

Write-Log "Run upgrade by user: $env:UserName"
# Run python Heartbeat
.\emar.exe --upgrade-program

$PID | Out-File (Join-Path $cfg.backups_path "upgrade.pid")
Pop-Location