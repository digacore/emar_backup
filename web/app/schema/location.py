from pydantic import BaseModel


class LocationInfo(BaseModel):
    name: str
    company_name: str | None

    total_computers: int
    total_computers_offline: int
    primary_computers_offline: int
    default_sftp_path: str

    class Config:
        orm_mode = True
