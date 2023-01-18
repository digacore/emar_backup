from datetime import datetime
from pydantic import BaseModel


class DownloadStatus(BaseModel):
    client: str
    location: str
    download_status: str
    last_time_online: datetime
    identifier_key: str
