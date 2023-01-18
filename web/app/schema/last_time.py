from datetime import datetime
from pydantic import BaseModel


class LastTime(BaseModel):
    client: str
    location: str
    last_download_time: datetime
    last_time_online: datetime
    identifier_key: str
