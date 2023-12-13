import requests

from urllib.parse import urljoin

from app import logger

from app.consts import MANAGER_HOST, IDENTIFIER_KEY


@logger.catch
def computer_delete():
    URL = urljoin(
        MANAGER_HOST,
        f"delete_computer?identifier_key={IDENTIFIER_KEY}",
    )
    response = requests.get(
        URL,
    )
    if response.status_code == 200:
        logger.info("Computer {} deleted from manager.", IDENTIFIER_KEY)
    else:
        logger.error(
            "Failed to delete computer {} from manager.",
            IDENTIFIER_KEY,
        )
    logger.info("Delete computer finished")
