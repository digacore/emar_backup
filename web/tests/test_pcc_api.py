import pytest

from app import models as m, schema as s
from app.controllers import get_pcc_2_legged_token
from config import BaseConfig as CFG


SHOULD_SKIP_TESTS = (
    not CFG.PCC_BASE_URL
    or not CFG.PCC_CLIENT_ID
    or not CFG.PCC_CLIENT_SECRET
    or not CFG.CERTIFICATE_PATH
    or not CFG.PRIVATEKEY_PATH
)


@pytest.mark.skipif(SHOULD_SKIP_TESTS, reason="PCC API credentials not set")
def test_get_pcc_2_legged_token(client):
    # Get 2-legged access token first time
    token = get_pcc_2_legged_token()

    assert token
    assert isinstance(token, str)
    assert len(token) > 0

    saved_token = m.PCCAccessToken.query.first()
    assert saved_token
    assert saved_token.token == token

    # Get 2-legged access token second time (should be returned from DB)
    second_time_token = get_pcc_2_legged_token()
    assert second_time_token
    assert second_time_token == token


@pytest.mark.skipif(SHOULD_SKIP_TESTS, reason="PCC API credentials not set")
def test_download_backup_from_pcc(client, pcc_test_computer):
    # Test successful download backup from PCC API
    response = client.post(
        "/download_backup",
        json=s.GetCredentials(
            identifier_key=pcc_test_computer.identifier_key,
            computer_name=pcc_test_computer.computer_name,
        ).json(),
    )
    assert response and response.status_code == 200
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=emar_backup.zip"
    )
    assert response.content_type == "application/zip"
    assert response.stream

    # Test computer that dosn't exist
    not_found_response = client.post(
        "/download_backup",
        json=s.GetCredentials(
            identifier_key="not_existing_key",
            computer_name="not_existing_computer_name",
        ).json(),
    )
    assert not_found_response and not_found_response.status_code == 404

    # Test computer with no PCC API data
    not_pcc_test_computer = m.Computer.query.filter_by(
        computer_name="comp6_late"
    ).first()

    conflict_response = client.post(
        "/download_backup",
        json=s.GetCredentials(
            identifier_key=not_pcc_test_computer.identifier_key,
            computer_name=not_pcc_test_computer.computer_name,
        ).json(),
    )

    assert conflict_response and conflict_response.status_code == 409
