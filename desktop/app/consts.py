import os
import platform
import json

from pathlib import Path

from app import logger

STORAGE_PATH = str(Path("C:\\") / "eMARVault")
if not os.path.exists(STORAGE_PATH):
    os.mkdir(STORAGE_PATH)

CREDS_FILE = "creds.json"
IP_BLACKLISTED = "red - ip blacklisted"
COMPSTAT_FILE = os.path.join(STORAGE_PATH, "compstat.json")
LOCAL_CREDS_JSON = os.path.join(STORAGE_PATH, CREDS_FILE)
COMPUTER_NAME = platform.node()

INPUT_LOG_FILE_PATH = Path("C://eMARVault") / "emar_log.txt"
OUTPUT_LOG_FILE_PATH = Path(os.environ["AppData"]) / "Emar" / "application.txt"


if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        G_MANAGER_HOST = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception(
            "Can't find manager_host in config.json. \
                Check that field and file exist."
        )
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")
