Push-Location $PSScriptRoot
$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$PID | Out-File (Join-Path $cfg.backups_path "task.pid")

$LOG_FILE = "UpdateLog.txt"

. .\Common.ps1

Write-Log Run update by user: $env:UserName

# Run python updater
.\emar.exe --server-connect


Pop-Location
