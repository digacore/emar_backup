pyinstaller --noconfirm --onefile --console `
--distpath "." `
--collect-all "paramiko" `
--collect-all "requests" `
--collect-all "loguru" `
--collect-all "win32com" `
server_connect.py