param
(
    [Parameter(Mandatory=$false)][string]$propertyValue
)

Push-Location $PSScriptRoot


$logFileName = "UpdateLog.txt"

$DataDir = Join-Path $ENV:AppData "Emar"
New-Item -ItemType Directory -Path $DataDir -Force
$logFile = Join-Path  $DataDir $logFileName

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Run update by user: $env:UserName"

# Run python updater
.\server_connect.exe 


Pop-Location
