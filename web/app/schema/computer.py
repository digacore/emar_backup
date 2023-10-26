from datetime import datetime, timedelta
from pydantic import BaseModel

from app.models import DeviceRole, ComputerStatus


class ComputerInfo(BaseModel):
    computer_name: str
    location_name: str | None
    company_name: str | None

    download_status: str | None
    last_download_time: datetime | None
    offline_period: int

    device_role: DeviceRole

    status: ComputerStatus

    last_week_offline_occurrences: int | None
    last_week_offline_time: timedelta | None

    class Config:
        orm_mode = True


class ComputerRegInfo(BaseModel):
    identifier_key: str
    computer_name: str


class ComputerSpecialStatus(BaseModel):
    identifier_key: str
    computer_name: str
    special_status: str
