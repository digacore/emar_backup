import json
import os
import platform
from functools import lru_cache
from pathlib import Path

from app import schemas as s

STORAGE_PATH = Path("C:\\") / "eMARVault"
if not STORAGE_PATH.exists():
    STORAGE_PATH.mkdir()

CREDS_FILE = "creds.json"
IP_BLACKLISTED = "red - ip blacklisted"
COMPSTAT_FILE = Path(STORAGE_PATH) / "compstat.json"
LOCAL_CREDS_JSON = Path(STORAGE_PATH) / CREDS_FILE
COMPUTER_NAME = platform.node()

INPUT_LOG_FILE_PATH = Path("C://eMARVault") / "emar_log.txt"
OUTPUT_LOG_FILE_PATH = Path(os.environ["AppData"]) / "Emar" / "application.txt"

G_MANAGER_HOST = "unknown"

CONFIG_JSON = Path("config.json")


@lru_cache
def get_config_json() -> s.ConfigFile:
    assert CONFIG_JSON.exists()  # config.json must exist
    with open(CONFIG_JSON, "r") as f:
        config_json = json.load(f)  # raises JSONDecodeError if file is not valid JSON
    return s.ConfigFile.model_validate(config_json)  # raises ValidationError if file has wrong structure


CONFIG = get_config_json()

G_MANAGER_HOST = CONFIG.manager_host


def get_credentials() -> s.ConfigFile:
    assert LOCAL_CREDS_JSON.exists()  # creds.json must exist
    with open(LOCAL_CREDS_JSON, "r") as f:
        creds_json = json.load(f)
    return s.CredsFile.model_validate(creds_json)


CREDENTIALS = get_credentials()

MANAGER_HOST = CREDENTIALS.manager_host or str(G_MANAGER_HOST)
IDENTIFIER_KEY = CREDENTIALS.identifier_key
