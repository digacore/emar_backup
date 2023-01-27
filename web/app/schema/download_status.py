from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DownloadStatus(BaseModel):
    company_name: str
    location_name: str
    download_status: str
    last_time_online: datetime
    identifier_key: str
    last_downloaded: Optional[str]

