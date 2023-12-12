import json
from urllib.parse import urljoin

import requests

from app import logger

from app.consts import LOCAL_CREDS_JSON


@logger.catch
def computer_delete():
    try:
        creds_json = None

        with open(LOCAL_CREDS_JSON, "r") as f:
            creds_json = json.load(f)
        manager_host = creds_json["manager_host"]

        if creds_json:
            URL = urljoin(
                manager_host,
                f"delete_computer?identifier_key={creds_json['identifier_key']}",
            )
            response = requests.get(
                URL,
            )
            if response.status_code == 200:
                logger.info(
                    "Computer {} deleted from manager.", creds_json["identifier_key"]
                )
            else:
                logger.error(
                    "Failed to delete computer {} from manager.",
                    creds_json["identifier_key"],
                )
        else:
            logger.error("Computer_delete app can not find creds.json file.")
        logger.info("Delete computer finished")
    except Exception as e:
        logger.error("Exception occurred: {}", e)
