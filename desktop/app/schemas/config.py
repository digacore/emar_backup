from pydantic import BaseModel
from .location_info import LocationInfo


class ConfigFile(BaseModel):
    version: str
    manager_host: str
    backups_path: str
    message: str | None = None
    msi_version: str | None = None
    identifier_key: str = "unknown"
    computer_name: str | None = None
    status: str | None = None
    host: str | None = None
    company_name: str | None = None
    location_name: str | None = None
    sftp_username: str | None = None
    sftp_password: str | None = None
    sftp_folder_path: str | None = None
    folder_password: str | None = None
    files_checksum: dict[str, str] | None = None
    use_pcc_backup: bool | None = None
    lid: int | None = None
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = False
    additional_locations: list[LocationInfo] | None = None
    additional_sftp_folder_paths: list[str] | None = None
