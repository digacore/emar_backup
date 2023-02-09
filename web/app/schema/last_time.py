from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LastTime(BaseModel):
    computer_name: Optional[str]
    company_name: Optional[str]
    location_name: Optional[str]
    last_download_time: Optional[datetime]
    last_time_online: datetime
    identifier_key: str
