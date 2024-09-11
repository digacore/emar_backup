from pydantic import BaseModel

from app.schema.location import LocationInfo


class ComputerCredentialsInfo(BaseModel):
    status: str
    message: str
    host: str
    company_name: str
    location_name: str
    additional_locations: list[LocationInfo]
    sftp_username: str | None
    sftp_password: str | None
    sftp_folder_path: str | None
    additional_folder_paths: list[str]
    identifier_key: str
    computer_name: str
    folder_password: str
    manager_host: str
    files_checksum: dict[str, str]
    msi_version: str
    use_pcc_backup: bool
    pcc_fac_id: str | None
    version: str
