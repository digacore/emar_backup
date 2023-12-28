
if (Test-Path '.\msi\dist') {
    Remove-Item .\msi\dist -Recurse
}

.\Inc-Version.ps1

pyinstaller --noconfirm --onefile --console `
    --distpath "msi/dist"    `
    --collect-all "paramiko" `
    --collect-all "requests" `
    --collect-all "loguru"   `
    --collect-all "win32com" `
    --collect-all "pydantic" `
    emar.py


copy .\config.json .\msi\dist\
copy .\eMARVault_256x256.ico .\msi\dist\

.\msi\BuildInstaller.ps1
