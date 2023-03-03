Remove-Item .\msi\dist -Recurse

pyinstaller --noconfirm --onefile --console `
--distpath "msi/dist" `
--collect-all "paramiko" `
--collect-all "requests" `
--collect-all "loguru" `
--collect-all "win32com" `
server_connect.py

pyinstaller --noconfirm --onefile --console `
--distpath "msi/dist" `
--collect-all "requests" `
--collect-all "loguru" `
heartbeat.py

copy .\config.json .\msi\dist\
