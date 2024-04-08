from pydantic import BaseModel
from .location_info import LocationInfo


class ConfigResponse(BaseModel):
    version: str | None = None
    manager_host: str
    backups_path: str | None = None
    message: str
    msi_version: str = "stable"
    identifier_key: str
    computer_name: str
    status: str
    host: str | None = None
    company_name: str | None = None
    location_name: str | None = None
    sftp_username: str | None = None
    sftp_password: str | None = None
    sftp_folder_path: str | None = None
    folder_password: str | None = None
    files_checksum: dict[str, str] | None = None
    use_pcc_backup: bool | None = None
    additional_locations: list[LocationInfo] | None = None
    additional_sftp_folder_paths: list[str] | None = None
