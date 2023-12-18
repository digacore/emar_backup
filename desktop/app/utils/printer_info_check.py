import requests

from urllib.parse import urljoin

from app.logger import logger
from app.consts import CREDENTIALS, MANAGER_HOST
from app.utils import get_printer_info_by_posh, send_printer_info


def printer_info_check():
    url = urljoin(MANAGER_HOST, "get_telemetry_info")
    response = requests.get(
        url,
        json=CREDENTIALS.model_dump(include={"identifier_key"}),
    )
    if response.status_code == 404:
        logger.info(
            "Failed to retrieve telemetry info from server. Response: {}",
            response.json(),
        )
    else:
        printer_info = get_printer_info_by_posh()
        logger.info("Printer info: {}", printer_info)
        # send printer info to server
        send_printer_info(MANAGER_HOST, CREDENTIALS, printer_info)
