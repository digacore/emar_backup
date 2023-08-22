import os
import requests
from urllib.parse import urljoin
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.logger import logger
from app import models as m, schema as s
from app.utils import get_base64_string
from config import BaseConfig as CFG


def get_pcc_2_legged_token() -> str:
    """Retrieve valid 2-legged access token for PCC API

    Returns:
        str: PCC API 2-legged access token
    """
    # Try to get existing token
    token = m.PCCAccessToken.query.first()
    if token and (token.created_at + timedelta(seconds=token.expires_in)) > (
        datetime.now() + timedelta(seconds=60)
    ):
        logger.debug(
            "Existing token is valid till: {}",
            token.created_at + timedelta(seconds=token.expires_in),
        )
        return token.token

    server_path = os.path.join("auth", "token")
    url = urljoin(CFG.PCC_BASE_URL, server_path)
    base64_secret = get_base64_string(f"{CFG.PCC_CLIENT_ID}:{CFG.PCC_CLIENT_SECRET}")

    # If token is expired or not exists - get new one
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Basic {base64_secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
        )
        access_token_info = s.TwoLeggedAuthResult.parse_obj(response.json())
    except ValidationError as e:
        logger.error("Can't get PCC API access token. Reason: {}", e)
        raise e

    # Save new token to DB
    if not token:
        token = m.PCCAccessToken(
            token=access_token_info.access_token,
            expires_in=access_token_info.expires_in,
        )
        token.save()
    else:
        token.token = access_token_info.access_token
        token.expires_in = access_token_info.expires_in
        token.created_at = datetime.now()
        token.save()

    return token.token
