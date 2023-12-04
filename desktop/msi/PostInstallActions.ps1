Push-Location $PSScriptRoot

$LOG_FILE = "InstallLog.txt"

. .\Common.ps1

Write_Log start
Wrtite-Log "User: [$env:UserName]"

Unregister-ScheduledTask -TaskName "eMARVaultHourlyCheck" -Confirm:$false -ErrorAction Continue
Write-Log "Unregister-ScheduledTask eMARVaultHourlyCheck"

$scriptDir = Join-Path "." "." -Resolve
Write-Log "scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\TaskAction.ps1" `
  -WorkingDirectory $scriptDir
Write-Log "action - [$action]"`

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Hours 1) -At 0am
Write-Log "trigger - [$trigger]"

$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -RunLevel Highest
Write-Log "principal - [$principal]"

$executionTimeLimit = New-TimeSpan -Hours 2
Write-Log "executionTimeLimit - [$executionTimeLimit]"

$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit
Write-Log "taskSettings - [$taskSettings]"

$task = Register-ScheduledTask  -TaskName "eMARVaultHourlyCheck" -Description "Periodically check remote sftp and update backups" `
  -Action $action `
  -Principal $principal `
  -Trigger $trigger `
  -Settings $taskSettings 2>&1 | Tee-Object -Append -filePath $logFile

Write-Log "Register-ScheduledTask - [$task]"

Unregister-ScheduledTask -TaskName "eMARVaultHeartbeat" -Confirm:$false -ErrorAction Continue
Write-Log "Unregister-ScheduledTask eMARVaultHeartbeat"

$scriptDir = Join-Path "." "." -Resolve
Write-Log "scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\Heartbeat.ps1" `
  -WorkingDirectory $scriptDir
Write-Log "action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 5) -At 0am
Write-Log "trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "eMARVaultHeartbeat" `
  -Settings $(New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit) `
  -Principal $principal -Description "Periodically notify server that local machine is alive"
Write-Log "Register-ScheduledTask - [$task]"

Start-ScheduledTask -TaskName "eMARVaultHourlyCheck"

Write-Log finish

Pop-Location
