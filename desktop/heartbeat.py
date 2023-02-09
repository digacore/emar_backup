import os
import datetime
from pathlib import Path
import json
import requests
from loguru import logger


class EST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours = -5)

    def tzname(self, dt):
        return "EST"

    def dst(self, dt):
        return datetime.timedelta(0)

# storage_path = os.path.join(os.environ.get("APPDATA"), Path("EmarDir"))
storage_path = os.path.join(Path("C:\\"), Path("EmarDir"))

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(storage_path, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)
        return False
    return True


mknewdir(storage_path)

if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception("Can't find manager_host in config.json. Check that field and file exist.")
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


creds_file = "creds.json"
local_creds_json = os.path.join(storage_path, creds_file)

@logger.catch
def send_activity():
    creds_json = None

    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    if creds_json:
        url = f"{manager_host}/last_time"
        requests.post(url, json={
        "computer_name": creds_json["computer_name"],
        "identifier_key": creds_json["identifier_key"],
        "last_time_online": str(datetime.datetime.now(EST()))
        })
        logger.info("User last time online sent.")
    else:
        logger.error("Heartbeat app can not find creds.json file.")

send_activity()
