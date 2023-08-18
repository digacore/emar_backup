Push-Location $PSScriptRoot

$logFileName = "InstallLog.txt"

$DataDir = Join-Path $ENV:AppData "Emar"
New-Item -ItemType Directory -Path $DataDir -Force
$logFile = Join-Path  $DataDir $logFileName
if (!(Test-Path $logFile)) {
  New-Item -path $DataDir -name $logFileName -type "file"
}
Write-Host $logFile

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - start"
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - User: [$env:UserName]"

Unregister-ScheduledTask -TaskName "eMARVaultHourlyCheck" -Confirm:$false -ErrorAction Continue
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Unregister-ScheduledTask"

$scriptDir = Join-Path "." "." -Resolve
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\TaskAction.ps1" `
  -WorkingDirectory $scriptDir
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Hours 1) -At 0am
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - trigger - [$trigger]"

$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -RunLevel Highest
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - principal - [$principal]"

$executionTimeLimit = New-TimeSpan -Hours 2
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - executionTimeLimit - [$executionTimeLimit]"

$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - taskSettings - [$taskSettings]"

$task = Register-ScheduledTask  -TaskName "eMARVaultHourlyCheck" -Description "Periodically check remote sftp and update backups" `
-Action $action `
-Trigger $trigger `
-Settings $taskSettings 2>&1 | tee -Append -filePath $logFile

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"

Start-Sleep -Seconds 300

Unregister-ScheduledTask -TaskName "eMARVaultHeartbeat" -Confirm:$false -ErrorAction Continue
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Unregister-ScheduledTask"

$scriptDir = Join-Path "." "." -Resolve
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\Heartbeat.ps1" `
  -WorkingDirectory $scriptDir
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 5) -At 0am
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "eMARVaultHeartbeat" `
-Settings $(New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit) `
-Principal $principal -Description "Periodically notify server that local machine is alive"
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"

Start-ScheduledTask -TaskName "eMARVaultHourlyCheck"

Pop-Location

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - finish"