import requests

from app import logger


@logger.catch
def send_printer_info(manager_host, creds_json, printer_info):
    url = f"{manager_host}/printer_info"
    response = requests.post(
        url,
        json={
            "computer_name": creds_json["computer_name"],
            "identifier_key": creds_json["identifier_key"],
            "printer_info": printer_info,
        },
    )
    logger.info("Printer info sent. Response: {}", response.json())
