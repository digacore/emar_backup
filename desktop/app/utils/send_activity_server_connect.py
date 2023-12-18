import datetime
from urllib.parse import urljoin
import requests

from app.consts import MANAGER_HOST, CREDENTIALS
from app.logger import logger

from app.utils.send_activity import offset_to_est


def send_activity_server_connect(last_download_time: str) -> None:
    URL = urljoin(MANAGER_HOST, "last_time")
    now = offset_to_est(datetime.datetime.utcnow())
    res = requests.post(
        URL,
        json={
            "computer_name": CREDENTIALS.computer_name,
            "company_name": CREDENTIALS.company_name,
            "identifier_key": CREDENTIALS.identifier_key,
            "location_name": CREDENTIALS.location_name,
            "last_download_time": last_download_time,
            "last_time_online": now,
        },
    )
    if res.status_code != 200:
        logger.error(f"Error sending last time download: {res.status_code}")
    else:
        logger.info("User last time download sent.")
