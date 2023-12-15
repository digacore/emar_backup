import os
import json
import requests

from urllib.parse import urljoin

from app.logger import logger
from app.consts import COMPSTAT_FILE, LOCAL_CREDS_JSON, G_MANAGER_HOST, MANAGER_HOST
from app.utils import (
    get_printer_info_by_posh,
    send_activity,
    changes_lookup,
    send_printer_info,
)


def heartbeat():
    creds_json = None
    if os.path.isfile(LOCAL_CREDS_JSON):
        with open(LOCAL_CREDS_JSON, "r") as f:
            creds_json = json.load(f)
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else str(G_MANAGER_HOST)
    else:
        manager_host = str(G_MANAGER_HOST)

    if not os.path.isfile(COMPSTAT_FILE):
        with open(COMPSTAT_FILE, "w") as f:
            f.write("{}")

    comp_remote_data = send_activity(manager_host, creds_json)
    changes_lookup(comp_remote_data)

    # logic for printer check
    url = urljoin(str(MANAGER_HOST), "get_telemetry_info")
    response = requests.get(
        url,
        json={
            "identifier_key": creds_json["identifier_key"],
        },
    )
    if response.status_code == 404:
        logger.info(
            "Failed to retrieve telemetry info from server. Response: {}",
            response.json(),
        )
    else:
        if response.json()["send_printer_info"]:
            printer_info = get_printer_info_by_posh()
            if printer_info:
                logger.info("Printer info: {}", printer_info)
                # send printer info to server
                send_printer_info(str(MANAGER_HOST), creds_json, printer_info)
