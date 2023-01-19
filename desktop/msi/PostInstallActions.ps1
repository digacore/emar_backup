param
(
    [Parameter(Mandatory=$false)][string]$propertyValue
)

Push-Location $PSScriptRoot

# $fileName = "FileToInstall.txt"
# $dateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"

# if(Test-Path $fileName)
# {
#     Add-Content -Path $fileName -Value "$dateTime - $propertyValue"
# }
# else
# {
#     throw "File $fileName does not exist"
# }

Unregister-ScheduledTask -TaskName "CheckRemoteUpdate" -Confirm:$false -ErrorAction SilentlyContinue

$scriptPath = Join-Path "." TaskAction.ps1 -Resolve

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy ByPass `"$scriptPath`""

$trigger =  New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 1) -At 0am

Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CheckRemoteUpdate" -Description "Periodically check remote update"

Pop-Location
