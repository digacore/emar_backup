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

Function MsgBox($Message, $Title) {
  # ApplicationModal, DefaultButton1, OkOnly, OkCancel, AbortRetryIgnore, YesNoCancel, YesNo, RetryCancel, Critical, Question, Exclamation, Information, 
  # DefaultButton2, DefaultButton3, SystemModal, MsgBoxHelp, MsgBoxSetForeground, MsgBoxRight, MsgBoxRtlReading
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
$username = $cred.username
$password = $cred.GetNetworkCredential().password

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - Test Creds for user: [$username]"

if ( (-not $cred) -or (-not (Test-Credential $cred) ) ) {
  MsgBox "Wrong Credentials" "Installation canceled"
  exit 1
}

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

$task = Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CheckRemoteUpdate" -Description "Periodically check remote update" -User $username -Password $password
Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") Register-ScheduledTask - [$task]"

Pop-Location

Add-Content -Path $logFile -Value "`n$(Get-Date -Format `"yyyy-MM-dd HH:mm:ss K`") - finish"