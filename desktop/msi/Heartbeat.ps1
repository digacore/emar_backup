Push-Location $PSScriptRoot
$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$PID | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")

$logFileName = "UpdateLog.txt"

$DataDir = Join-Path $ENV:AppData "Emar"
New-Item -ItemType Directory -Path $DataDir -Force
$logFile = Join-Path  $DataDir $logFileName

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Run heartbeat by user: $env:UserName"

# Run python Heartbeat
.\heartbeat.exe
# TODO: Create process and wait for it to finish. put pid in heartbeat.pid file
# $proc = Start-Process -FilePath "heartbeat.exe"
# $proc.Id | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")
# Wait-Process $proc

$PID | Out-File (Join-Path $cfg.backups_path "heartbeat.pid")
Pop-Location
