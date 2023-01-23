pyinstaller --noconfirm --onefile --console `
    --collect-all "paramiko" `
    --collect-all "requests" `
    --collect-all "python-dotenv" `
    --collect-all "loguru" `
    server_connect.py