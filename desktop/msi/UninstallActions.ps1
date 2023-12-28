Push-Location $PSScriptRoot

$LOG_FILE = "UninstallLog.txt"

. .\Common.ps1

# ----- begin -----
Write-Log start
Write-Log "User: [$env:UserName]"

# -- delete copmuter from web --
Write-Log "Run computer_delete script by user: $env:UserName"
# Run python Heartbeat
.\emar.exe --computer-delete
Write-Log "Run computer_delete script by user: $env:UserName - done"

# -- wait for scheduled tasks to stop before unregistration scheduled tasks --

$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$pidFile = Join-Path $cfg.backups_path "heartbeat.pid"
if (Test-Path $pidFile) {
  $procId = Get-Content $pidFile
  Write-Log "Wait for heartbeat to stop [$procId]"
  if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
    if (!(Wait-Process -Id $procId -Timeout 0 -ErrorAction SilentlyContinue)) {
      Write-Log "Kill heartbeat process [$procId]"
      Kill-Tree $procId
    }
  }
}

$pidFile = Join-Path $cfg.backups_path "task.pid"
if (Test-Path $pidFile) {
  $procId = Get-Content $pidFile
  Write-Log "Wait for task to stop [$procId]"
  if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
    if (!(Wait-Process -Id $procId -Timeout 0 -ErrorAction SilentlyContinue)) {
      Write-Log "Kill task process [$procId]"
      Kill-Tree $procId
    }
  }
}

# -- delete scheduled tasks --
Write-Log "Unregister-ScheduledTask eMARVaultHourlyCheck"
Unregister-ScheduledTask -TaskName "eMARVaultHourlyCheck" -Confirm:$false -ErrorAction SilentlyContinue
if (! $?) {
  Write-Log "Unregister-ScheduledTask eMARVaultHourlyCheck failed"
}
Write-Log "Unregister-ScheduledTask eMARVaultHeartbeat"
Unregister-ScheduledTask -TaskName "eMARVaultHeartbeat" -Confirm:$false -ErrorAction SilentlyContinue
if (! $?) {
  Write-Log "Unregister-ScheduledTask eMARVaultHeartbeat failed"
}

# -- wait for scheduled tasks to stop after delete tasks --

$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
$pidFile = Join-Path $cfg.backups_path "heartbeat.pid"
if (Test-Path $pidFile) {
  $procId = Get-Content $pidFile
  Write-Log "WARNING: Wait for heartbeat to stop [$procId]"
  if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
    Wait-Process -Id $procId
  }
}

$pidFile = Join-Path $cfg.backups_path "task.pid"
if (Test-Path $pidFile) {
  $procId = Get-Content $pidFile
  Write-Log "WARNING: Wait for task to stop [$procId]"
  if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
    Wait-Process -Id $procId
  }
}

# -- delete files --
Write-Log "Remove-Item $($cfg.backups_path) -Recurse -Force"
Remove-Item $cfg.backups_path -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
if (! $?) {
  Write-Log "Remove Folder $($cfg.backups_path) failed"
}

# -- delete shortcut from desktop --
$pathToShortcut = Join-Path $ENV:Public\Desktop "eMARVault.lnk"
Write-Log "Remove-Item $pathToShortcut"
Remove-Item $pathToShortcut -ErrorAction SilentlyContinue | Out-Null




Pop-Location
