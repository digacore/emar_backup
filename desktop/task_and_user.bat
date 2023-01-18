set USERNAME=copy_test
set DIRECTORY_NAME=backups
set DOMAIN_NAME=PDellcomp
set FOLDER_PATH=C:\Users\%USERNAME%\%DIRECTORY_NAME%
set TASK_FILE=server_connect.exe

net user %USERNAME% pass /add /passwordchg:no
@REM powershell -ExecutionPolicy Bypass -file G:\0_Python\simple2b\Nathan_Berger\desktop\user_profile.ps1
@REM powershell -ExecutionPolicy Bypass -command "Create-NewProfile -Username copy_test2 -Password start123"

timeout 5

@REM net localgroup group-name /add

@REM net localgroup Users %USERNAME% /add

mkdir %FOLDER_PATH%
@REM cd /d %FOLDER_PATH%
@REM copy simple_msi.msi C:\Users\%USERNAME%

icacls %FOLDER_PATH% /setowner %USERNAME%
icacls %FOLDER_PATH% /grant %USERNAME%:(OI)(CI)F /T
icacls %FOLDER_PATH% /inheritance:r

@REM change user to admin
@REM runas /noprofile /user:%DOMAIN_NAME%\%USERNAME% icacls %FOLDER_PATH% /grant %USERNAME%:(OI)(CI)F /T
@REM runas /netonly /user:%USERNAME% C:\Users\%USERNAME%\simple_msi.msi

@REM SchTasks /Create /SC HOURLY /TN "Check remote for updates" /TR "C:Users/%USERNAME%/%TASK_FILE%"
SchTasks /Create -u /SC HOURLY /TN "Check remote for updates" /TR "%PROGRAMFILES%\Simple2B\FTP Load Backups\%TASK_FILE%"

echo Script is finished. Terminate in 5 sec
timeout 60