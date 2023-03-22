from pydantic import BaseModel


class UpdateMSIVersion(BaseModel):
    current_msi_version: str
    identifier_key: str
