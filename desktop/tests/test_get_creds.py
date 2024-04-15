import requests


from urllib.parse import urljoin

from app import schemas as s
from app.consts import COMPUTER_NAME, MANAGER_HOST, IDENTIFIER_KEY


def test_get_credentials():
    URL = urljoin("http://127.0.0.1:5000", "/get_credentials")
    data = s.GetCredentialsData(
        computer_name=COMPUTER_NAME,
        identifier_key="4269e11f-5baf-4954-b8fb-039faae69e82",
    )
    response = requests.post(
        URL,
        json=data.model_dump(),
    )
    # response = client.post(
    #     "/get_credentials",
    #     json=dict(identifier_key="comp4_identifier_key", computer_name="comp4_test"),
    # )

    assert response
