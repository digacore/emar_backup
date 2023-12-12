import os

# import time
# import random
import json
from pathlib import Path
from loguru import logger

from app.consts import COMPSTAT_FILE, LOCAL_CREDS_JSON, STORAGE_PATH
from app.utils import (
    get_printer_info_by_posh,
    send_activity,
    changes_lookup,
    send_printer_info,
)

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(STORAGE_PATH, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True,
)


def heartbeat():
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
    try:
        # NOTE wait randomly from 0 to 279 sec
        # to spread load on the server
        # time.sleep(random.uniform(0, 279))
        creds_json = None
        printer_info = get_printer_info_by_posh()

        if os.path.isfile(LOCAL_CREDS_JSON):
            with open(LOCAL_CREDS_JSON, "r") as f:
                creds_json = json.load(f)
            manager_host = (
                creds_json["manager_host"]
                if creds_json["manager_host"]
                else g_manager_host
            )
        else:
            manager_host = g_manager_host

        if not os.path.isfile(COMPSTAT_FILE):
            with open(COMPSTAT_FILE, "w") as f:
                f.write("{}")

        comp_remote_data = send_activity(manager_host, creds_json)
        changes_lookup(comp_remote_data)

        if printer_info:
            logger.info("Printer info: {}", printer_info)
            # send printer info to server
            send_printer_info(manager_host, creds_json, printer_info)
            logger.info("Task finished")
        # time.sleep(5)
    except Exception as e:
        logger.error("Exception occurred: {}", e)
        # time.sleep(20)
