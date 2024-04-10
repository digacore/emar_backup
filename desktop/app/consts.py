import json
import os
import platform

from pydantic import ValidationError
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

# get path to work directory
BASE_DIR = Path(__file__).parent.parent
SEVEN_ZIP = BASE_DIR / "7z.exe"

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
    file_path = LOCAL_CREDS_JSON
    if not LOCAL_CREDS_JSON.exists():
        file_path = CONFIG_JSON
    with open(file_path, "r") as f:
        creds_json = json.load(f)
    try:
        creds_data = s.ConfigFile.model_validate(creds_json)
    except ValidationError:
        config_data_dict = CONFIG.model_dump(exclude_none=True)
        config_data_dict.update(creds_json)
        with open(LOCAL_CREDS_JSON, "w") as f:
            json.dump(config_data_dict, f, indent=2)
        creds_data = s.ConfigFile.model_validate(config_data_dict)
    return creds_data


CREDENTIALS = get_credentials()

MANAGER_HOST = CREDENTIALS.manager_host or G_MANAGER_HOST
if CREDENTIALS.identifier_key == "unknown":
    CREDENTIALS.identifier_key = None
IDENTIFIER_KEY = CREDENTIALS.identifier_key
if not CREDENTIALS.computer_name:
    CREDENTIALS.computer_name = COMPUTER_NAME

ZIP_FILE_NAME = "emar_backups.zip"
