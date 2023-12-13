import requests
import datetime

from urllib.parse import urljoin
from app.logger import logger


def offset_to_est(dt_now: datetime.datetime):
    """Offset to EST time

    Args:
        dt_now (datetime.datetime): datetime.datetime.utcnow()

    Returns:
        datetime.datetime: EST datetime
    """
    est_norm_datetime = dt_now - datetime.timedelta(hours=5)
    return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")


@logger.catch
def send_activity(manager_host, creds_json=None):
    if creds_json:
        URL = urljoin(manager_host, "last_time")

        last_time_online = offset_to_est(datetime.datetime.utcnow())
        response = requests.post(
            URL,
            json={
                "computer_name": creds_json["computer_name"],
                "identifier_key": creds_json["identifier_key"],
                "last_time_online": last_time_online,
            },
        )
        logger.info("User last time online {} sent.", last_time_online)

        return response.json()
    else:
        logger.error("Heartbeat app can not find creds.json file.")
