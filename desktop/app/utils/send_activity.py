import requests
import datetime
import json

from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from app.consts import COMPSTAT_FILE
from app.logger import logger
from app import schemas as s


def offset_to_est(dt_now: datetime.datetime) -> str:
    """Return current time in Eastern (EST/EDT) as string.

    Args:
        dt_now (datetime.datetime): datetime.datetime.utcnow()

    Returns:
        str: Eastern time as "YYYY-MM-DD HH:MM:SS"
    """
    if dt_now.tzinfo is None:
        dt_now = dt_now.replace(tzinfo=ZoneInfo("UTC"))
    eastern = dt_now.astimezone(ZoneInfo("America/New_York"))
    return eastern.strftime("%Y-%m-%d %H:%M:%S")


@logger.catch
def send_activity(manager_host: str, creds_json: s.ConfigFile | None = None) -> s.LastTimeResponse:
    if creds_json:
        URL = urljoin(manager_host, "last_time")
        now = datetime.datetime.utcnow()

        data = s.ActivityData(
            computer_name=creds_json.computer_name,
            identifier_key=creds_json.identifier_key,
            last_time_online=offset_to_est(now),
        )
        response = requests.post(
            URL,
            json=data.model_dump(),
        )
        logger.info("User last time online {} sent.", data.last_time_online)
        if response.status_code != 200:
            logger.error("Failed to send last time online. Response: {}", response.json())
            return
        res = s.LastTimeResponse.model_validate(response.json())
        with open(COMPSTAT_FILE, "w") as f:
            json.dump(
                {
                    "sftp_host": res.sftp_host,
                    "sftp_username": res.sftp_username,
                    "sftp_folder_path": res.sftp_folder_path,
                    "manager_host": res.manager_host,
                    "msi_version": res.msi_version or "stable",
                },
                f,
            )
            logger.info("Updated computer data was written to compstat.json")
    else:
        logger.error("Heartbeat app can not find creds.json file.")
