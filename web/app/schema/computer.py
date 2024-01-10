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
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = False


class ComputerRegInfoLid(BaseModel):
    computer_name: str
    identifier_key: str
    lid: int
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = True


class ComputerSpecialStatus(BaseModel):
    identifier_key: str
    computer_name: str
    special_status: str
