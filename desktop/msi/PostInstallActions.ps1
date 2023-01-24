param
(
    [Parameter(Mandatory=$false)][string]$propertyValue
)

Push-Location $PSScriptRoot

$logFileName = "InstallLog.txt"

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$logFile = Join-Path $DesktopPath $logFileName
if (!(Test-Path $logFile))
{
   New-Item -path $DesktopPath -name $logFileName -type "file"
}

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - start"

Unregister-ScheduledTask -TaskName "CheckRemoteUpdate" -Confirm:$false -ErrorAction SilentlyContinue
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Unregister-ScheduledTask"

$scriptDir = Join-Path "." "." -Resolve
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\TaskAction.ps1" `
  -WorkingDirectory $scriptDir
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - action - [$action]"

$trigger =  New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Hours 1) -At 0am
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CheckRemoteUpdate" -Description "Periodically check remote update"
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"

Pop-Location

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - finish"