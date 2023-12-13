from pathlib import Path
from pydantic import BaseModel, AnyUrl


class ConfigFile(BaseModel):
    version: str
    manager_host: AnyUrl
    backups_path: Path
