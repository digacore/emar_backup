$USERNAME = "copy_test"
$PASSWORD = "pass"
$S_PASSWORD = ConvertTo-SecureString -String "pass" -AsPlainText -Force
$DIRECTORY_NAME = "backups"
$DOMAIN_NAME = "PDellcomp"
$FOLDER_PATH = "C:\$DIRECTORY_NAME"
$TASK_FILE = "server_connect.exe"

New-LocalUser -Name $USERNAME -Password $S_PASSWORD -ErrorAction stop
Add-LocalGroupMember -Group Users -Member $USERNAME
Get-LocalUser -Name $USERNAME

# timeout 5

mkdir $FOLDER_PATH

icacls.exe $FOLDER_PATH /setowner $USERNAME
icacls.exe $FOLDER_PATH /grant "$($USERNAME):(OI)(CI)F" /T
icacls.exe $FOLDER_PATH /inheritance:r

$pyscript = "C:\Program Files\Simple2B\FTP Load Backups\server_connect.exe"

$USERNAME = "copy_test"
$PASSWORD = "pass"
$TASKNAME = "Check remote for updates"
$TASKACTION = "$($env:PROGRAMFILES)\Simple2B\FTP Load Backups\$($TASK_FILE)"

Unregister-ScheduledTask -TaskName $TASKNAME -Confirm:$false -ErrorAction SilentlyContinue

# cmd /c SchTasks /ru copy_test /rp $PASSWORD /Create /SC minute /mo 2 /TN $TASKNAME /TR $TASKACTION
cmd /c SchTasks /ru copy_test /rp $PASSWORD /Create /SC HOURLY /TN $TASKNAME /TR $TASKACTION


# $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1)
# $PS = cmd.exe
# Register-ScheduledTask -TaskName "LoadBackup123" –Action $PS
# Register-ScheduledTask -TaskName "LoadBackup" -Trigger $trigger -User $USERNAME -Password $PASSWORD –Action $PS

Write-Output "Script is finished. Terminate in 10 sec"
timeout 10

