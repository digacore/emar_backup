import os
import pytest
from dotenv import load_dotenv

from app import models as m, schema as s
from app.controllers import (
    get_pcc_2_legged_token,
    get_activations,
    get_org_facilities_list,
    create_pcc_org_facs,
)


load_dotenv()

# These tests require PCC API credentials to be set in .env
# And presence of Certificate Name of the certificate that is used to sign the requests
# in PCC Sandbox settings
IS_NOT_CURRENT_CERT_IN_PCC = False

SANDBOX_ORG_UUID = "11848592-809A-42F4-82E3-5CE14964A007"

SHOULD_SKIP_TESTS = (
    IS_NOT_CURRENT_CERT_IN_PCC
    or not os.environ.get("PCC_BASE_URL", None)
    or not os.environ.get("PCC_CLIENT_ID", None)
    or not os.environ.get("PCC_CLIENT_SECRET", None)
    or not os.environ.get("PCC_APP_NAME", None)
    or not os.environ.get("CERTIFICATE_PATH", None)
    or not os.environ.get("PRIVATEKEY_PATH", None)
)


@pytest.mark.skipif(False, reason="PCC API credentials not set")
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
        "/pcc_api/download_backup",
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
        "/pcc_api/download_backup",
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
        "/pcc_api/download_backup",
        json=s.GetCredentials(
            identifier_key=not_pcc_test_computer.identifier_key,
            computer_name=not_pcc_test_computer.computer_name,
        ).json(),
    )

    assert conflict_response and conflict_response.status_code == 409


# TODO: create normal tests for this
@pytest.mark.skip
def test_get_activations(client):
    # Test successful get activations list from PCC API
    activations_list = get_activations()
    assert isinstance(activations_list, list)


@pytest.mark.skip
def test_get_org_facilities(client):
    # Test successful get org facilities list from PCC API
    org_facilities_list = get_org_facilities_list(SANDBOX_ORG_UUID)
    assert isinstance(org_facilities_list, list)


@pytest.mark.skip
def test_create_pcc_org_facs(client):
    create_pcc_org_facs()
