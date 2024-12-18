Push-Location $PSScriptRoot

$LOG_FILE = "InstallLog.txt"

. .\Common.ps1

Write-Log start
Write-Log "User: [$env:UserName]"

Write-Log "Creating desktop shortcut"
$cfg = Get-Content config.json | Out-String | ConvertFrom-Json
if (Test-Path -Path $cfg.backups_path) {
    Continue
}
else {
    New-Item -ItemType Directory -Path $cfg.backups_path
}
$IconLocation = (Get-Item "eMARVault_256x256.ico").FullName
$ShortcutPath = Join-Path $env:PUBLIC Desktop\eMARVault.lnk

$shell = New-Object -comObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $cfg.backups_path
$shortcut.IconLocation = $IconLocation
$shortcut.WorkingDirectory = $cfg.backups_path
$shortcut.Save()
Write-Log "Desktop shortcut created"


# Copy pdf to desktop
$HowToUsePath = (Get-Item "eMARVault_How_to_Use.pdf").FullName
# check if file exists
if (-not (Test-Path -Path $HowToUsePath)) {
    Write-Log "Warning: How to use pdf not found"
    exit 1
}

$UserProfilesPath = "C:\Users"
$UserDirs = Get-ChildItem -Path $UserProfilesPath | Where-Object { $_.PSIsContainer -and (Test-Path "$($_.FullName)\Desktop") }

# Копіювати файл для кожного користувача
foreach ($UserDir in $UserDirs) {
    $DesktopDir = "$($UserDir.FullName)\Desktop"
    $OneDriveDesktop = "$($UserDir.FullName)\OneDrive\Desktop"

    if (Test-Path -Path $OneDriveDesktop) {
        Copy-Item -Path $HowToUsePath -Destination $OneDriveDesktop -Force
        Write-Log "Copied to OneDrive desktop: $OneDriveDesktop"
    }

    if (Test-Path -Path $cfg.backups_path) {
        Copy-Item -Path $HowToUsePath -Destination $cfg.backups_path -Force
        Write-Log "Copied to backup folder: $DesktopDir"
    }

    if (Test-Path -Path $DesktopDir) {
        Copy-Item -Path $HowToUsePath -Destination $DesktopDir -Force
        Write-Log "Copied to desktop: $DesktopDir"
    }
}


# Get location is from msi CommandLine
Get-WmiObject Win32_Process -Filter "name = 'msiexec.exe'" | Select-Object CommandLine | ForEach-Object { $_.CommandLine -match '^.+lid_(\d+)\.msi.*$' }
if ($Matches) {
    $lid = $Matches[1]
    Write-Log "lid - [$lid]"
    $cfg = Get-Content config.json | Out-String | ConvertFrom-Json
    if (-not $cfg.PSObject.Properties["lid"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "lid" -Value $null
    }
    $cfg.lid = $lid
    $cfg | ConvertTo-Json | Set-Content config.json
}
else {
    Write-Log "Warning: lid not found"
}

$registryPath = "HKCU:\Software\Emar\emarVault"
$registryValueName = "MyArgument"

try {
    $registryValue = Get-ItemPropertyValue -Path $registryPath -Name $registryValueName -ErrorAction Stop
    Write-Host "Registry value: $($registryValue)"
}
catch {
    Write-Host "Failed to read registry value: $_"
}


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

$taskSettings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit
Write-Log "taskSettings - [$taskSettings]"

$task = Register-ScheduledTask  -TaskName "eMARVaultHourlyCheck" -Description "Periodically check remote sftp and update backups" `
    -Action $action `
    -Principal $principal `
    -Trigger $trigger `
    -Settings $taskSettings

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


Unregister-ScheduledTask -TaskName "eMARVaultUpgrade" -Confirm:$false -ErrorAction Continue
Write-Log "Unregister-ScheduledTask eMARVaultUpgrade"

$scriptDir = Join-Path "." "." -Resolve
Write-Log "scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
    -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\Upgrade.ps1" `
    -WorkingDirectory $scriptDir
Write-Log "action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Days 1) -At 0am #need to be changed
Write-Log "trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "eMARVaultUpgrade" `
    -Settings $(New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit $executionTimeLimit) `
    -Principal $principal -Description "Periodically check for updates and upgrade the program"
Write-Log "Register-ScheduledTask - [$task]"



Write-Log finish


# Run python Heartbeat
Write-Log "Run heartbeat script by user: $env:UserName"
.\emar.exe -hb
Write-Log "Run heartbeat script by user: $env:UserName - done"

# Run python Heartbeat
Write-Log "Run server connect script by user: $env:UserName"
.\emar.exe -sc
Write-Log "Run server connect script by user: $env:UserName - done"


Pop-Location
