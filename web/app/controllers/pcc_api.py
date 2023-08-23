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


def get_activations() -> list[s.OrgActivationData]:
    """Get the list of all existing AppActivations (companies)

    Raises:
        e (ValidationError): response parsing error while getting data from PCC API.

    Returns:
        list[s.OrgActivationData]: list of all existing AppActivations
    """
    # Retrieve 2-legged access token
    token = get_pcc_2_legged_token()

    # Get the list of all existing AppActivations
    activations_list: list[s.OrgActivationData] = []
    should_download = True

    server_path: str = os.path.join(
        "api", "public", "preview1", "applications", CFG.PCC_APP_NAME, "activations"
    )
    url: str = urljoin(CFG.PCC_BASE_URL, server_path)
    page = 1

    while should_download:
        try:
            res = requests.get(
                url,
                params={"page": page, "page_size": 200},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
            )

            parsed_res = s.ActivationsResponse.parse_obj(res.json())
        except ValidationError as e:
            logger.error("Can't get data from PCC API. Reason: {}", e)
            raise e

        activations_list.extend(parsed_res.data)
        page += 1
        should_download = parsed_res.paging.hasMore

    return activations_list


def get_org_facilities_list(pcc_org_uuid: str) -> list[s.Facility]:
    """Get the list of all organization facilities

    Args:
        pcc_org_uuid (str): PCC organization UUID

    Raises:
        e (ValidationError): response parsing error while getting data from PCC API.

    Returns:
        list[s.Facility]: list of all organization facilities
    """
    # Get access token
    token = get_pcc_2_legged_token()

    # Get the list of all organization facilities
    facilities_list: list[s.Facility] = []
    should_download = True

    server_path: str = os.path.join(
        "api", "public", "preview1", "orgs", pcc_org_uuid, "facs"
    )
    url: str = urljoin(CFG.PCC_BASE_URL, server_path)
    page = 1

    while should_download:
        try:
            res = requests.get(
                url,
                params={"page": page, "page_size": 200},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
            )

            parsed_res = s.FacilitiesListResponse.parse_obj(res.json())
        except ValidationError as e:
            logger.error("Can't get data from PCC API. Reason: {}", e)
            raise e

        facilities_list.extend(parsed_res.data)
        page += 1
        should_download = parsed_res.paging.hasMore

    return facilities_list


def get_facility_info(pcc_org_uuid: str, pcc_facility_id: str) -> s.Facility:
    """Get facility information

    Args:
        pcc_org_uuid (str): PCC organization UUID
        pcc_facility_id (str): PCC facility ID

    Raises:
        e (ValidationError): response parsing error while getting data from PCC API.

    Returns:
        s.Facility: facility information
    """
    # Get access token
    token = get_pcc_2_legged_token()

    server_path: str = os.path.join(
        "api", "public", "preview1", "orgs", pcc_org_uuid, "facs", pcc_facility_id
    )
    url: str = urljoin(CFG.PCC_BASE_URL, server_path)

    try:
        res = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
        )

        parsed_res = s.Facility.parse_obj(res.json())
    except ValidationError as e:
        logger.error("Can't get data from PCC API. Reason: {}", e)
        raise e

    return parsed_res


def create_pcc_org_facs():
    """Create PCC organizations and facilities in DB"""

    # Get the list of all existing AppActivations
    activations_list = get_activations()

    # Check the existence of the organization in DB and create if not exists
    for organization in activations_list:
        facilities_list = (
            organization.facilityInfo
            if organization.scope != 1
            else get_org_facilities_list(organization.orgUuid)
        )

        company = m.Company.query.filter_by(pcc_org_id=organization.orgUuid).first()
        if not company:
            if isinstance(facilities_list[0], s.Facility):
                company_name = facilities_list[0].orgName
            elif isinstance(facilities_list[0], s.FacilityActivationData):
                facility_info = get_facility_info(
                    organization.orgUuid, facilities_list[0].facId
                )
                company_name = facility_info.orgName
            else:
                raise Exception(
                    "Can't get company name from PCC API. Unknown response type"
                )
            company = m.Company(
                pcc_org_id=organization.orgUuid,
                name=company_name,
            )
            company.save()

            logger.info(
                "Company [{}] created. PCC orgUuid: {}",
                company.name,
                company.pcc_org_id,
            )

        # Check the existence of the facility in DB and create if not exists
        for facility in facilities_list:
            location = m.Location.query.filter(
                m.Location.company_name == company.name,
                m.Location.pcc_fac_id == facility.facId,
            ).first()
            if not location:
                if isinstance(facility, s.Facility):
                    location = m.Location(
                        name=facility.facilityName,
                        company_name=company.name,
                        pcc_fac_id=facility.facId,
                        use_pcc_backup=True,
                    )
                else:
                    facility_info = get_facility_info(
                        organization.orgUuid, facility.facId
                    )
                    location = m.Location(
                        name=facility_info.facilityName,
                        company_name=company.name,
                        pcc_fac_id=facility.facId,
                        use_pcc_backup=True,
                    )

                location.save()

                logger.info(
                    "Location [{}] created. PCC facId: {}",
                    location.name,
                    location.pcc_fac_id,
                )
