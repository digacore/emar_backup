import requests

from urllib.parse import urljoin

from app.logger import logger
from app.consts import MANAGER_HOST
from app.utils import get_printer_info_by_posh, send_printer_info


def printer_info_check(credentials=None):
    from app.consts import CREDENTIALS
    creds = credentials if credentials is not None else CREDENTIALS
    url = urljoin(MANAGER_HOST, "get_telemetry_info")
    # TODO: Change get->post for more proper handling
    response = requests.get(
        url,
        json=creds.model_dump(include={"identifier_key"}),
    )
    if response.status_code == 404:
        logger.info(
            "Failed to retrieve telemetry info from server. Response: {}",
            response.text[:32],
        )
    else:
        printer_info = get_printer_info_by_posh()
        logger.info("Printer info: {}", printer_info)
        # send printer info to server
        send_printer_info(MANAGER_HOST, creds, printer_info)
