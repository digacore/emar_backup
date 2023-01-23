from datetime import datetime
from pydantic import BaseModel


class ComputerFullInfo(BaseModel):
    computer_name: str
    location_name:str

    type: str
    alert_status: str
    activated: bool
    created_at: str

    sftp_host: str
    sftp_username: str
    sftp_password: str
    sftp_folder_path: str
    folder_password: str

    download_status: str
    last_download_time: str
    last_time_online: str
    identifier_key: str

    company_name: str


class ComputerRegInfo(BaseModel):
    identifier_key: str
    computer_name: str
