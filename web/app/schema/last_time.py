from datetime import datetime
from pydantic import BaseModel


class LastTime(BaseModel):
    company_name: str
    location_name: str
    last_download_time: datetime
    last_time_online: datetime
    identifier_key: str
