@ECHO OFF

PUSHD "%~dp0"

powershell -ExecutionPolicy ByPass .\BuildInstaller.ps1

POPD