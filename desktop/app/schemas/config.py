from pathlib import Path
from pydantic import BaseModel, AnyUrl


class ConfigFile(BaseModel):
    version: str
    manager_host: AnyUrl
    backups_path: Path
    message: str | None = None
    msi_version: str | None = None
    identifier_key: str = "unknown"
    computer_name: str | None = None
    status: str | None = None
