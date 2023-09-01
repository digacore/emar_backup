import os
import json
import requests
from urllib.parse import urljoin
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.logger import logger
from app import models as m, schema as s
from app.utils import get_base64_string
from app.controllers.system_log import create_system_log
from config import BaseConfig as CFG


class UnknownTypeError(Exception):
    pass


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
        "api", "public", "preview1", "orgs", pcc_org_uuid, "facs", str(pcc_facility_id)
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


def create_pcc_orgs_facs() -> None:
    """
    Create companies and locations from PCC API data

    Returns:
        list[s.PccCreatedObject]: list of created objects
    """

    # Get the list of all existing AppActivations
    activations_list = get_activations()

    # Check the existence of the organization in DB and create if not exists
    for organization in activations_list:
        # List of created objects
        created_objects: list[s.PccCreatedObject] = []

        facilities_list = (
            organization.facilityInfo
            if organization.scope != 1
            else get_org_facilities_list(organization.orgUuid)
        )

        if isinstance(facilities_list[0], s.Facility):
            company_name = facilities_list[0].orgName
        elif isinstance(facilities_list[0], s.FacilityActivationData):
            facility_info = get_facility_info(
                organization.orgUuid, facilities_list[0].facId
            )
            company_name = facility_info.orgName
        else:
            raise UnknownTypeError(
                "Can't get company name from PCC API. Unknown response type"
            )

        # There can be companies which are already exist but do not have pcc_org_id
        company_by_org_uuid = m.Company.query.filter_by(
            pcc_org_id=organization.orgUuid
        ).first()
        company_by_name = m.Company.query.filter_by(name=company_name).first()

        if not company_by_org_uuid and not company_by_name:
            new_company = m.Company(
                pcc_org_id=organization.orgUuid,
                name=company_name,
            )
            new_company.save()

            created_objects.append(
                s.PccCreatedObject(
                    type="Company",
                    action="Created",
                    pcc_org_id=new_company.pcc_org_id,
                    id=new_company.id,
                    name=new_company.name,
                ).dict()
            )

            create_system_log(m.SystemLogType.COMPANY_CREATED, new_company, None)

            logger.info(
                "Company [{}] created. PCC orgUuid: {}",
                new_company.name,
                new_company.pcc_org_id,
            )
        elif company_by_name and not company_by_org_uuid:
            company_by_name.pcc_org_id = organization.orgUuid
            company_by_name.update()

            created_objects.append(
                s.PccCreatedObject(
                    type="Company",
                    action="Updated",
                    pcc_org_id=company_by_name.pcc_org_id,
                    id=company_by_name.id,
                    name=company_by_name.name,
                ).dict()
            )

            create_system_log(m.SystemLogType.COMPANY_UPDATED, company_by_name, None)

            logger.info(
                "Company [{}] updated. PCC orgUuid: {}",
                company_by_name.name,
                company_by_name.pcc_org_id,
            )

        company = m.Company.query.filter_by(pcc_org_id=organization.orgUuid).first()

        # Check the existence of the facility in DB and create if not exists or update if doesn't have pcc_fac_id
        for facility in facilities_list:
            location_by_fac_id = m.Location.query.filter(
                m.Location.company_name == company.name,
                m.Location.pcc_fac_id == facility.facId,
            ).first()
            location_by_name = m.Location.query.filter(
                m.Location.company_name == company.name,
                m.Location.name == facility.facilityName,
            ).first()

            # Create new location if not exists
            if not location_by_fac_id and not location_by_name:
                if isinstance(facility, s.Facility):
                    new_location = m.Location(
                        name=facility.facilityName,
                        company_name=company.name,
                        pcc_fac_id=facility.facId,
                        use_pcc_backup=True,
                    )
                else:
                    facility_info = get_facility_info(
                        organization.orgUuid, facility.facId
                    )
                    new_location = m.Location(
                        name=facility_info.facilityName,
                        company_name=company.name,
                        pcc_fac_id=facility.facId,
                        use_pcc_backup=True,
                    )

                new_location.save()

                created_objects.append(
                    s.PccCreatedObject(
                        type="Location",
                        action="Created",
                        id=new_location.id,
                        pcc_fac_id=new_location.pcc_fac_id,
                        name=new_location.name,
                    ).dict()
                )

                create_system_log(m.SystemLogType.LOCATION_CREATED, new_location, None)

                logger.info(
                    "Location [{}] created. PCC facId: {}",
                    new_location.name,
                    new_location.pcc_fac_id,
                )

            # Update location if it doesn't have pcc_fac_id
            elif location_by_name and not location_by_fac_id:
                location_by_name.pcc_fac_id = facility.facId
                location_by_name.update()

                created_objects.append(
                    s.PccCreatedObject(
                        type="Location",
                        action="Updated",
                        id=location_by_name.id,
                        pcc_fac_id=location_by_name.pcc_fac_id,
                        name=location_by_name.name,
                    ).dict()
                )

                create_system_log(
                    m.SystemLogType.LOCATION_UPDATED, location_by_name, None
                )

                logger.info(
                    "Location [{}] updated. PCC facId: {}",
                    location_by_name.name,
                    location_by_name.pcc_fac_id,
                )

        if created_objects:
            # Save creation report to DB
            report = m.PCCCreationReport(
                data=json.dumps(created_objects),
                company_id=company.id,
                company_name=company.name,
            )
            report.save()

            logger.info("Creation report {} saved to DB", report.id)


def gen_pcc_creation_report(scan_record_id: int):
    """
    Generate PCC creation report and set status in scan instance
    after the creation process is finished
    """
    # Get scan record with "IN_PROGRESS" status from DB
    scan_record = m.PCCActivationsScan.query.get(scan_record_id)

    # Create PCC orgs and facilities and fill reports data
    try:
        create_pcc_orgs_facs()
    except Exception as e:
        logger.error("Can't create PCC orgs and facilities. Reason: {}", e)
        scan_record.status = m.ScanStatus.FAILED
        scan_record.finished_at = datetime.utcnow()
        scan_record.error = str(e)
        scan_record.save()
        raise e

    scan_record.status = m.ScanStatus.SUCCEED
    scan_record.finished_at = datetime.utcnow()
    scan_record.save()
    logger.info("PCC orgs and facilities created successfully")
