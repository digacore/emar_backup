import os
import json
import requests

from app import logger
from urllib.parse import urljoin

from app import schemas as s
from app.consts import COMPUTER_NAME, LOCAL_CREDS_JSON, G_MANAGER_HOST


def register_computer():
    logger.debug("Computer Name {}, type {}", COMPUTER_NAME, type(COMPUTER_NAME))
    if not isinstance(COMPUTER_NAME, str):
        raise (
            ValueError(
                "Can't get computer name. Name {}, type {}",
                COMPUTER_NAME,
                type(COMPUTER_NAME),
            )
        )
    identifier_key = "new_computer"

    # TODO: replace f string in request with urljoin
    URL = urljoin(G_MANAGER_HOST, "register_computer")
    response = requests.post(
        URL,
        json={
            "computer_name": COMPUTER_NAME,
            "identifier_key": identifier_key,
        },
    )

    if response.status_code == 200:
        logger.info(
            "New computer registered. Download will start next time \
                if credentials inserted to DB."
        )
    else:
        logger.warning(
            "Something went wrong. Response status code = {}", response.status_code
        )

    return response


def get_credentials():
    logger.info("Receiving credentials.")
    creds_json = None

    if os.path.isfile(LOCAL_CREDS_JSON):
        with open(LOCAL_CREDS_JSON, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials received from {LOCAL_CREDS_JSON}.")

        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else G_MANAGER_HOST
        )

        URL = urljoin(manager_host, "get_credentials")

        response = requests.post(
            URL,
            json={
                "computer_name": computer_name,
                "identifier_key": str(identifier_key),
            },
        )

        if response.status_code == 500 or response.status_code == 400:
            raise ConnectionAbortedError(response.text)

        if "rmcreds" in response.json():
            if os.path.isfile(LOCAL_CREDS_JSON):
                os.remove(LOCAL_CREDS_JSON)
                logger.warning(
                    "Remote server can't find computer {}. \
                        Deleting creds.json and registering current computer.",
                    computer_name,
                )
                register_computer()

    else:
        response = register_computer()

    config_data = s.ConfigResponse.model_validate(response.json())
    if (
        config_data.message == "Supplying credentials"
        or config_data.message == "Computer registered"
    ):
        with open(LOCAL_CREDS_JSON, "w") as f:
            json.dump(config_data.model_dump(), f, indent=2)
            logger.info(
                f"Full credentials received from server and {LOCAL_CREDS_JSON} updated."
            )

        creds_json = creds_json if creds_json else dict()

        return config_data.model_dump(), creds_json

    else:
        raise ValueError(
            "Wrong response data. Can't proceed without correct credentials."
        )
