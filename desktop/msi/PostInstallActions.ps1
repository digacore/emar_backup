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

# Window with options for computer
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Select a Device Optinons'
$form.Size = New-Object System.Drawing.Size(350, 350)
$form.StartPosition = 'CenterScreen'

$okButton = New-Object System.Windows.Forms.Button
$okButton.Location = New-Object System.Drawing.Point(75, 275)
$okButton.Size = New-Object System.Drawing.Size(75, 23)
$okButton.Text = 'OK'
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.AcceptButton = $okButton
$form.Controls.Add($okButton)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(150, 275)
$cancelButton.Size = New-Object System.Drawing.Size(75, 23)
$cancelButton.Text = 'Cancel'
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.CancelButton = $cancelButton
$form.Controls.Add($cancelButton)

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(10, 10)
$label.Size = New-Object System.Drawing.Size(280, 20)
$label.Text = 'Please select a device type:'
$form.Controls.Add($label)

$comboBox = New-Object System.Windows.Forms.ComboBox
$comboBox.Location = New-Object System.Drawing.Point(10, 30)
$comboBox.Size = New-Object System.Drawing.Size(260, 20)
$comboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList

[void]$comboBox.Items.Add('DESKTOP')
[void]$comboBox.Items.Add('LAPTOP')

$form.Controls.Add($comboBox)

$label2 = New-Object System.Windows.Forms.Label
$label2.Location = New-Object System.Drawing.Point(10, 60)
$label2.Size = New-Object System.Drawing.Size(280, 20)
$label2.Text = 'Please select a device role:'
$form.Controls.Add($label2)

$comboBox2 = New-Object System.Windows.Forms.ComboBox
$comboBox2.Location = New-Object System.Drawing.Point(10, 80)
$comboBox2.Size = New-Object System.Drawing.Size(260, 20)
$comboBox2.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList

[void]$comboBox2.Items.Add('PRIMARY')
[void]$comboBox2.Items.Add('ALTERNATE')

$form.Controls.Add($comboBox2)

# Add label for Device location
$label3 = New-Object System.Windows.Forms.Label
$label3.Location = New-Object System.Drawing.Point(10, 200)
$label3.Size = New-Object System.Drawing.Size(280, 20)
$label3.Text = 'Device location (optional):'
$form.Controls.Add($label3)

# Add TextBox for Device location
$textBox = New-Object System.Windows.Forms.TextBox
$textBox.Location = New-Object System.Drawing.Point(10, 220)
$textBox.Size = New-Object System.Drawing.Size(260, 20)
$form.Controls.Add($textBox)

$checkBox1 = New-Object System.Windows.Forms.CheckBox
$checkBox1.Location = New-Object System.Drawing.Point(20, 120)
$checkBox1.Size = New-Object System.Drawing.Size(200, 40)
$checkBox1.Text = "Enable logs for this device"
$form.Controls.Add($checkBox1)

$checkBox2 = New-Object System.Windows.Forms.CheckBox
$checkBox2.Location = New-Object System.Drawing.Point(20, 160)
$checkBox2.Size = New-Object System.Drawing.Size(200, 40)
$checkBox2.Text = "Activate this device"
$form.Controls.Add($checkBox2)

$form.Topmost = $true

$result = $form.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    $selectedDeviceType = $comboBox.SelectedItem
    $selectedDeviceRole = $comboBox2.SelectedItem
    $enableLogs = $checkBox1.Checked
    $activateDevice = $checkBox2.Checked
    $deviceLocation = $textBox.Text

    $message = "Selected Device Type: $selectedDeviceType`n"
    $message += "Selected Device Role: $selectedDeviceRole`n"
    $message += "Enable Logs: $enableLogs`n"
    $message += "Activate Device: $activateDevice`n"
    $message += "Device Location: $deviceLocation"

    # write collected data to config.json
    $cfg = Get-Content config.json | Out-String | ConvertFrom-Json
    if (-not $cfg.PSObject.Properties["device_type"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "device_type" -Value $null
    }
    $cfg.device_type = $selectedDeviceType
    if (-not $cfg.PSObject.Properties["device_role"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "device_role" -Value $null
    }
    $cfg.device_role = $selectedDeviceRole
    if (-not $cfg.PSObject.Properties["enable_logs"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "enable_logs" -Value $null
    }
    $cfg.enable_logs = $enableLogs
    if (-not $cfg.PSObject.Properties["activate_device"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "activate_device" -Value $null
    }
    $cfg.activate_device = $activateDevice
    if (-not $cfg.PSObject.Properties["device_location"]) {
        $cfg | Add-Member -MemberType NoteProperty -Name "device_location" -Value $null
    }
    $cfg.device_location = $deviceLocation
    $cfg | ConvertTo-Json | Set-Content config.json

    [System.Windows.Forms.MessageBox]::Show($message, "Results", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}

# Add logic after the form is submitted
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    $selectedRole = $comboBox2.SelectedItem

    if ($selectedRole -eq 'PRIMARY') {
        # Disable sleep mode
        Write-Host "Disabling sleep mode for PRIMARY device"
        powercfg /change standby-timeout-ac 0
        powercfg /change standby-timeout-dc 0
        powercfg /change monitor-timeout-ac 0
        powercfg /change monitor-timeout-dc 0
    }
    else {
        Write-Host "No changes to sleep settings"
    }
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

$wshell = New-Object -ComObject Wscript.Shell
$wshell.Popup("Program is successfully installed!")

# Run python Heartbeat
Write-Log "Run heartbeat script by user: $env:UserName"
.\emar.exe -hb
Write-Log "Run heartbeat script by user: $env:UserName - done"

# Run python Heartbeat
Write-Log "Run server connect script by user: $env:UserName"
.\emar.exe -sc
Write-Log "Run server connect script by user: $env:UserName - done"


Pop-Location
