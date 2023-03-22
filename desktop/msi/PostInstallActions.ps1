param(
  [Parameter(Mandatory = $false)][string]$propertyValue
)

function Test-Credential {
  <#
    .SYNOPSIS
        Takes a PSCredential object and validates it against the local machine.

    .PARAMETER cred
        A PScredential object with the username/password you wish to test. Typically this is generated using the Get-Credential cmdlet. Accepts pipeline input.

    .OUTPUTS
        A boolean, indicating whether the credentials were successfully validated.

    #>
  param(
    [parameter(Mandatory = $true, ValueFromPipeline = $true)]
    [System.Management.Automation.PSCredential]$credential
  )
  begin {
    Add-Type -assemblyname system.DirectoryServices.accountmanagement
    $DS = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Machine) 
  }
  process {
    $password = $credential.GetNetworkCredential().password
    $DS.ValidateCredentials($credential.UserName, "$password")
  }
}

Function Get-UserCredential () {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'Need credentials'
    $form.Size = New-Object System.Drawing.Size(420, 250)
    $form.StartPosition = 'CenterScreen'

    $okButton = New-Object System.Windows.Forms.Button
    $okButton.Location = New-Object System.Drawing.Point(75, 120)
    $okButton.Size = New-Object System.Drawing.Size(75, 23)
    $okButton.Text = 'OK'
    $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.AcceptButton = $okButton
    $form.Controls.Add($okButton)

    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Location = New-Object System.Drawing.Point(200, 120)
    $cancelButton.Size = New-Object System.Drawing.Size(90, 23)
    $cancelButton.Text = 'Cancel'
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.CancelButton = $cancelButton
    $form.Controls.Add($cancelButton)

    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 20)
    $label.Size = New-Object System.Drawing.Size(350, 20)
    $label.Text = 'Please enter credatials for scheduled backup update'
    $form.Controls.Add($label)

    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 50)
    $label.Size = New-Object System.Drawing.Size(100, 20)
    $label.Text = 'Username: '
    $form.Controls.Add($label)

    $textBoxU = New-Object System.Windows.Forms.TextBox
    $textBoxU.Location = New-Object System.Drawing.Point(110, 50)
    $textBoxU.Size = New-Object System.Drawing.Size(160, 20)
    $textBoxU.Text = $env:UserName
    $form.Controls.Add($textBoxU)

    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 80)
    $label.Size = New-Object System.Drawing.Size(100, 20)
    $label.Text = 'Password: '
    $form.Controls.Add($label)

    $textBoxP = New-Object System.Windows.Forms.TextBox
    $textBoxP.Location = New-Object System.Drawing.Point(110, 80)
    $textBoxP.Size = New-Object System.Drawing.Size(160, 20)
    $textBoxP.PasswordChar = '*'
    $form.Controls.Add($textBoxP)

    $form.Topmost = $true

    $form.Add_Shown({$textBoxU.Select()})
    $result = $form.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK)
    {
        $username = $textBoxU.Text
        $password = ConvertTo-SecureString -String $textBoxP.Text -AsPlainText -Force
        New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password
    }
}

Function MsgBox($Message, $Title) {
  [void][System.Reflection.Assembly]::LoadWithPartialName("Microsoft.VisualBasic")
  [Microsoft.VisualBasic.Interaction]::MsgBox($Message, "SystemModal,Critical", $Title)
}

Push-Location $PSScriptRoot

$logFileName = "InstallLog.txt"

$DataDir = Join-Path $ENV:AppData "Emar"
New-Item -ItemType Directory -Path $DataDir -Force
$logFile = Join-Path  $DataDir $logFileName
if (!(Test-Path $logFile)) {
  New-Item -path $DataDir -name $logFileName -type "file"
}

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - start"
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Get User Creds. User: [$env:UserName]"
$cred = Get-Credential  -Message "Please enter credatials for scheduled backup update" -UserName $env:UserName
# $cred = $host.ui.PromptForCredential("Need credentials", "Please enter credatials for scheduled backup update.", "$env:UserName", "NetBiosUserName")
# $comp_name = [System.Net.Dns]::GetHostName()
# $cred = Invoke-Command -ComputerName $comp_name {Get-Credential Domain01\User02}

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Test Creds for user: [$username]"

if ( -not $cred )  {
    $cred = Get-UserCredential
}

if ( (-not $cred) -or (-not (Test-Credential $cred) ) ) {
  MsgBox "Wrong Credentials" "Installation canceled"
  exit 1
}

$username = $cred.username
$password = $cred.GetNetworkCredential().password

Unregister-ScheduledTask -TaskName "CheckRemoteUpdate" -Confirm:$false -ErrorAction SilentlyContinue
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Unregister-ScheduledTask"

$scriptDir = Join-Path "." "." -Resolve
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\TaskAction.ps1" `
  -WorkingDirectory $scriptDir
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Hours 1) -At 0am
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "eMARVaultHourlyCheck" `
-Description "Periodically check remote sftp and update backups" -User $username -Password $password `
-Settings $(New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"


Unregister-ScheduledTask -TaskName "Heartbeat" -Confirm:$false -ErrorAction SilentlyContinue
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Unregister-ScheduledTask"

$scriptDir = Join-Path "." "." -Resolve
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - scriptDir - [$scriptDir]"

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' `
  -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\Heartbeat.ps1" `
  -WorkingDirectory $scriptDir
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - action - [$action]"

$trigger = New-ScheduledTaskTrigger -Once -RepetitionInterval (New-TimeSpan -Minutes 5) -At 0am
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - trigger - [$trigger]"

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "eMARVaultHeartbeat" -Description "Periodically notify server that local machine is alive" -User $username -Password $password
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"

Pop-Location

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - finish"