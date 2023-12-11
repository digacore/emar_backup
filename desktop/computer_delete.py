import requests
from loguru import logger
import os
from pathlib import Path
import json
from urllib.parse import urljoin


STORAGE_PATH = str(Path("C:\\") / "eMARVault")

creds_file = "creds.json"
local_creds_json = os.path.join(STORAGE_PATH, creds_file)

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


@logger.catch
def main_func():
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
        URL = urljoin(
            manager_host,
            f"delete_computer?identifier_key={creds_json['identifier_key']}",
        )
        response = requests.delete(
            URL,
        )
        if response.status_code == 200:
            logger.info(
                "Computer {} deleted from manager.", creds_json["identifier_key"]
            )
        else:
            logger.error(
                "Failed to delete computer {} from manager.",
                creds_json["identifier_key"],
            )
    else:
        logger.error("Heartbeat app can not find creds.json file.")


try:
    main_func()
    logger.info("Delete computer finished")
except Exception as e:
    logger.error("Exception occurred: {}", e)
