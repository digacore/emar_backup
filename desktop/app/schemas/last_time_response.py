from pydantic import BaseModel


class LastTimeResponse(BaseModel):
    status: str
    message: str
    sftp_host: str
    sftp_username: str
    sftp_folder_path: str
    manager_host: str
    msi_version: str | None = None
