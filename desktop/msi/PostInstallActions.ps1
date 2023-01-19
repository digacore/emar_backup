param
(
    [Parameter(Mandatory=$false)][string]$propertyValue
)

Push-Location $PSScriptRoot

$fileName = "FileToInstall.txt"
$dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"

if (-not (Test-Path $fileName))
{
  throw "File $fileName does not exist"
}
Add-Content -Path $fileName -Value "`n$dateTime - start"


Unregister-ScheduledTask -TaskName "CheckRemoteUpdate" -Confirm:$false -ErrorAction SilentlyContinue
Add-Content -Path $fileName -Value "`n$dateTime Unregister-ScheduledTask"

# $scriptPath = Join-Path "." TaskAction.ps1 -Resolve
# Add-Content -Path $fileName -Value "`n$dateTime - scriptPath - [$scriptPath]"

# $action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
#   -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy ByPass `"$scriptPath`""
# Add-Content -Path $fileName -Value "`n$dateTime - action - [$action]"

# $trigger =  New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 1) -At 0am
# Add-Content -Path $fileName -Value "`n$dateTime - trigger - [$trigger]"

# $task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CheckRemoteUpdate" -Description "Periodically check remote update"
schtasks.exe /Create /SC minute /mo 2 /TN "CheckRemoteUpdate" /TR "C:\Program Files\CheckRemoteUpdate\PostInstallActions.ps1"
Add-Content -Path $fileName -Value "`n$dateTime Register-ScheduledTask - [$task]"

Pop-Location

Add-Content -Path $fileName -Value "`n$dateTime - finish"