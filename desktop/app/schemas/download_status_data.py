from pydantic import BaseModel


class DownloadStatusData(BaseModel):
    company_name: str
    location_name: str
    download_status: str
    last_time_online: str
    identifier_key: str
    last_downloaded: str
    last_saved_path: str
    error_message: str
