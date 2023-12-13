import os

import json

from app import logger
from app.consts import COMPSTAT_FILE, LOCAL_CREDS_JSON, G_MANAGER_HOST
from app.utils import (
    get_printer_info_by_posh,
    send_activity,
    changes_lookup,
    send_printer_info,
)


def heartbeat():
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
                else G_MANAGER_HOST
            )
        else:
            manager_host = G_MANAGER_HOST

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
