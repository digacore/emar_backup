from pydantic import BaseModel


class ConfigResponse(BaseModel):
    version: str | None = None
    manager_host: str
    backups_path: str | None = None
    message: str
    msi_version: str = "stable"
    identifier_key: str
    computer_name: str
    status: str
