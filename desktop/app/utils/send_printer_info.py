import requests

from urllib.parse import urljoin
from app.logger import logger
from app import schemas as s


@logger.catch
def send_printer_info(manager_host, creds_json: s.ConfigFile, printer_info: s.PrinterInfo):
    URL = urljoin(manager_host, "printer_info")
    data = s.PrinterInfoData(
        computer_name=creds_json.company_name,
        identifier_key=creds_json.identifier_key,
        printer_info=printer_info,
    )

    response = requests.post(
        URL,
        json=data.model_dump(by_alias=True),
    )
    logger.info("Printer info sent. Response: {}", response.json())
