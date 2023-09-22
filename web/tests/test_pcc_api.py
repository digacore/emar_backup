import pytest
import json

from app import models as m, schema as s
from app.controllers import (
    get_pcc_2_legged_token,
    get_activations,
    get_org_facilities_list,
    create_new_creation_reports,
    get_facility_info,
)


# NOTE: These tests are skipped by default because they require next things:
# 1. The machine should be under the USA VPN or in the USA localization
# 2. The machine should have the certificate that is used to sign the requests to PCC API
# 3. The Certificate Name (CN) should be set in PCC Sandbox settings
# 4. The PCC API credentials should be set in .env file (PCC_BASE_URL, PCC_CLIENT_ID, PCC_CLIENT_SECRET, PCC_APP_NAME)
# 5. The SANDBOX_ORG_UUID should be valid

SANDBOX_ORG_UUID = "11848592-809A-42F4-82E3-5CE14964A007"


@pytest.mark.skip
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


@pytest.mark.skip
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

    # Test computer that doesn't exist
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


@pytest.mark.skip
def test_get_activations(client):
    activations_list = get_activations()
    assert isinstance(activations_list, list)

    for activation in activations_list:
        assert isinstance(activation, s.OrgActivationData)


@pytest.mark.skip
def test_get_org_facilities(client):
    org_facilities_list = get_org_facilities_list(SANDBOX_ORG_UUID)
    assert isinstance(org_facilities_list, list)

    for facility in org_facilities_list:
        assert isinstance(facility, s.Facility)


@pytest.mark.skip
def test_get_facility_info(client):
    org_facilities_list = get_org_facilities_list(SANDBOX_ORG_UUID)
    assert isinstance(org_facilities_list, list)
    facility_id = org_facilities_list[0].facId

    facility_info = get_facility_info(SANDBOX_ORG_UUID, facility_id)
    assert isinstance(facility_info, s.Facility)


# @pytest.mark.skip
# def test_create_pcc_org_facs(client):
#     created_objects = create_new_approving_reports()
#     assert isinstance(created_objects, str)

#     # Check that all created objects are in DB
#     objects_list = json.loads(created_objects)
#     for obj in objects_list:
#         parsed_obj = s.PccCreatedObject.parse_obj(obj)
#         if parsed_obj.type == "Company":
#             assert m.Company.query.filter_by(pcc_org_id=parsed_obj.pcc_org_id).first()
#         else:
#             assert m.Location.query.filter_by(pcc_fac_id=parsed_obj.pcc_fac_id).first()
