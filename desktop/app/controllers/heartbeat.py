import os
import json


from app.logger import logger
from app.consts import COMPSTAT_FILE, MANAGER_HOST
from app.utils import (
    get_credentials,
    printer_info_check,
    send_activity,
)


@logger.catch
def heartbeat():
    if not os.path.isfile(COMPSTAT_FILE):
        with open(COMPSTAT_FILE, "w") as f:
            json.dump({}, f)
    credentials, _ = get_credentials()
    if not credentials:
        raise ValueError("Credentials not supplied. Can't continue.")
    send_activity(MANAGER_HOST, credentials)
    printer_info_check(credentials)
