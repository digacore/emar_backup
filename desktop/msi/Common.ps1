$DataDir = Join-Path $ENV:AppData "Emar"
New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
$logPathFile = Join-Path  $DataDir $LOG_FILE
New-Item -path $DataDir -name $LOG_FILE -type "file" -Force | Out-Null

function Write-Log {

    param (
        [Parameter(Mandatory, Position = 0)]
        [string]$message
    )

    Add-Content -Path $logPathFile -Value "$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - $message"
    # Write-Host "$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - $message"
}

function Kill-Tree {
    Param([int]$ppid)
    Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $ppid } | ForEach-Object { Kill-Tree $_.ProcessId }
    Stop-Process -Id $ppid
}
