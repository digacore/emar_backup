from datetime import datetime
from pydantic import BaseModel


class FilesChecksum(BaseModel):
    last_time_online: datetime
    identifier_key: str
    files_checksum: dict
