param
(
    [Parameter(Mandatory=$false)][string]$propertyValue
)

Push-Location $PSScriptRoot

# Run python updater
.\server_connect.exe 

$logFileName = "InstallLog.txt"

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$logFile = Join-Path $DesktopPath $logFileName

if(Test-Path $logFile)
{
    Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Action - $propertyValue"
}
else
{
    throw "File $logFile does not exist"
}

Pop-Location
