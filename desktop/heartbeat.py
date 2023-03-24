import os
import datetime
from pathlib import Path
import json
import requests
from loguru import logger


def offset_to_est(dt_now: datetime.datetime):
    """Offset to EST time

    Args:
        dt_now (datetime.datetime): datetime.datetime.now()

    Returns:
        datetime.datetime: EST datetime
    """
    est_norm_datetime = dt_now - datetime.timedelta(hours=5)
    return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")


STORAGE_PATH = os.path.join(Path("C:\\"), Path("eMARVault"))

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(STORAGE_PATH, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True,
)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)
        return False
    return True


mknewdir(STORAGE_PATH)

if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception(
            "Can't find manager_host in config.json. Check that field and file exist."
        )
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


creds_file = "creds.json"
local_creds_json = os.path.join(STORAGE_PATH, creds_file)


@logger.catch
def send_activity():
    creds_json = None

    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
        )
    else:
        manager_host = g_manager_host

    if creds_json:
        url = f"{manager_host}/last_time"
        last_time_online = offset_to_est(datetime.datetime.utcnow())
        requests.post(
            url,
            json={
                "computer_name": creds_json["computer_name"],
                "identifier_key": creds_json["identifier_key"],
                "last_time_online": last_time_online,
            },
        )
        logger.info("User last time online {} sent.", last_time_online)
    else:
        logger.error("Heartbeat app can not find creds.json file.")


send_activity()
