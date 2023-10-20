from datetime import datetime
from pydantic import BaseModel

from app.models import DeviceRole


class ComputerInfo(BaseModel):
    computer_name: str
    location_name: str | None
    company_name: str | None

    download_status: str | None
    last_download_time: datetime | None

    device_role: DeviceRole

    class Config:
        orm_mode = True


class ComputerRegInfo(BaseModel):
    identifier_key: str
    computer_name: str


class ComputerSpecialStatus(BaseModel):
    identifier_key: str
    computer_name: str
    special_status: str
