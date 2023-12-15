import os
import json
import requests

from app.logger import logger
from urllib.parse import urljoin

from app import schemas as s
from app.consts import COMPUTER_NAME, LOCAL_CREDS_JSON, MANAGER_HOST, CONFIG, IDENTIFIER_KEY


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
    URL = urljoin(str(MANAGER_HOST), "register_computer")
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
        logger.warning("Something went wrong. Response status code = {}", response.status_code)

    return response


def get_credentials() -> tuple[s.ConfigFile, s.ConfigFile]:  # return new and old values
    logger.info("Receiving credentials.")
    creds_json = CONFIG

    if LOCAL_CREDS_JSON.exists():
        # Computer already registered
        URL = urljoin(str(MANAGER_HOST), "get_credentials")
        data = s.GetCredentialsData(
            computer_name=COMPUTER_NAME,
            identifier_key=IDENTIFIER_KEY,
        )
        response = requests.post(
            URL,
            json=data.model_dump(),
        )

        if response.status_code >= 500:
            raise ConnectionAbortedError(f"status-code: {response.status_code}: {response.text}")

        if "rmcreds" in response.json():
            if os.path.isfile(LOCAL_CREDS_JSON):
                os.remove(LOCAL_CREDS_JSON)
                logger.warning(
                    "Remote server can't find computer {}. \
                        Deleting creds.json and registering current computer.",
                    COMPUTER_NAME,
                )
                response = register_computer()
                config_data = s.ConfigResponse.model_validate(response.json())
        if "message" in response.json() and response.json()["message"] == "Computer is not activated.":
            logger.warning("Computer is not activated. Server-connect script ended.")
            return None, None

        config_data = s.ConfigResponse.model_validate(response.json())

    else:
        # Computer is not registered yet
        response = register_computer()
        config_data = s.ConfigResponse.model_validate(response.json())

    if config_data.message == "Supplying credentials" or config_data.message == "Computer registered":
        config = CONFIG.model_dump()
        config.update(config_data.model_dump(exclude_none=True))
        with open(LOCAL_CREDS_JSON, "w") as f:
            json.dump(config, f, indent=2)
            logger.info(f"Full credentials received from server and {LOCAL_CREDS_JSON} updated.")

        return config, creds_json

    raise ValueError("Wrong response data. Can't proceed without correct credentials.")
