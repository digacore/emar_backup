from pydantic import BaseModel


class MsiDownloadData(BaseModel):
    name: str
    version: str
    flag: str
    identifier_key: str
    current_msi_version: str
