import datetime
from urllib.parse import urljoin
import requests
from app.consts import MANAGER_HOST
from app.logger import logger

from app.utils.send_activity import offset_to_est


def send_activity_server_connect(last_download_time, creds):
    URL = urljoin(str(MANAGER_HOST), "last_time")
    requests.post(
        URL,
        json={
            "computer_name": creds["computer_name"],
            "company_name": creds["company_name"],
            "identifier_key": creds["identifier_key"],
            "location_name": creds["location_name"],
            "last_download_time": last_download_time,
            "last_time_online": offset_to_est(datetime.datetime.utcnow()),
        },
    )
    logger.info("User last time download sent.")
