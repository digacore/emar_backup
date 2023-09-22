import os
import json
import requests
from urllib.parse import urljoin
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.logger import logger
from app import models as m, schema as s
from app.utils import get_base64_string
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


def create_new_creation_reports() -> None:
    """
    Retrieve current list of activations from PCC API and generate new reports for approve
    """

    # Get the list of all existing AppActivations
    activations_list = get_activations()

    # Check the existence of the organization in DB and create if not exists
    for organization in activations_list:
        # List of objects which should be created
        objects_to_approve: list[s.PCCReportObject] = []

        facilities_list = (
            organization.facilityInfo
            if organization.scope != 1
            else get_org_facilities_list(organization.orgUuid)
        )

        match type(facilities_list[0]):
            case s.Facility:
                company_name = facilities_list[0].orgName

            case s.FacilityActivationData:
                facility_info = get_facility_info(
                    organization.orgUuid, facilities_list[0].facId
                )

            case _:
                raise UnknownTypeError(
                    "Can't get company name from PCC API. Unknown response type"
                )

        # There can be companies which are already exist but do not have pcc_org_id
        company_by_org_uuid = m.Company.query.filter(
            m.Company.pcc_org_id == organization.orgUuid, m.Company.name == company_name
        ).first()

        # Try to find company just by name
        company_by_name = None
        if not company_by_org_uuid:
            company_by_name = m.Company.query.filter_by(name=company_name).first()

        if not company_by_org_uuid and not company_by_name:
            objects_to_approve.append(
                s.PCCReportObject(
                    type=s.PCCReportType.COMPANY.value,
                    action=s.PCCReportAction.CREATE.value,
                    pcc_org_id=organization.orgUuid,
                    name=company_name,
                ).dict()
            )

            logger.info(
                "Company [{}] added to approving list. PCC orgUuid: {}",
                company_name,
                organization.orgUuid,
            )
        elif company_by_name:
            objects_to_approve.append(
                s.PCCReportObject(
                    type=s.PCCReportType.COMPANY.value,
                    action=s.PCCReportAction.UPDATE.value,
                    pcc_org_id=organization.orgUuid,
                    name=company_name,
                    id=company_by_name.id,
                ).dict()
            )

            logger.info(
                "Company [{}] pcc_org_id should be updated. PCC orgUuid: {}",
                company_name,
                organization.orgUuid,
            )

        # Check the existence of the facility in DB and add to approving list if not exists
        for facility in facilities_list:
            location_by_fac_id = m.Location.query.filter(
                m.Location.company_name == company_name,
                m.Location.pcc_fac_id == facility.facId,
                m.Location.name == facility.facilityName,
            ).first()

            # Try to find location just by name
            location_by_name = None
            if not location_by_fac_id:
                location_by_name = m.Location.query.filter(
                    m.Location.company_name == company_name,
                    m.Location.name == facility.facilityName,
                ).first()

            # Add new location to approving list if not exists
            if not location_by_fac_id and not location_by_name:
                if isinstance(facility, s.Facility):
                    facility_info = facility
                    objects_to_approve.append(
                        s.PCCReportObject(
                            type=s.PCCReportType.LOCATION.value,
                            action=s.PCCReportAction.CREATE.value,
                            pcc_fac_id=facility.facId,
                            name=facility.facilityName,
                            pcc_org_id=organization.orgUuid,
                            use_pcc_backup=True,
                        ).dict()
                    )
                else:
                    facility_info = get_facility_info(
                        organization.orgUuid, facility.facId
                    )
                    objects_to_approve.append(
                        s.PCCReportObject(
                            type=s.PCCReportType.LOCATION.value,
                            action=s.PCCReportAction.CREATE.value,
                            pcc_fac_id=facility_info.facId,
                            name=facility_info.facilityName,
                            pcc_org_id=organization.orgUuid,
                            use_pcc_backup=True,
                        ).dict()
                    )

                logger.info(
                    "New location [{}] added to approving list. PCC facId: {}",
                    facility_info.facilityName,
                    facility_info.facId,
                )

            # Update location if it doesn't have pcc_fac_id
            elif location_by_name:
                objects_to_approve.append(
                    s.PCCReportObject(
                        type=s.PCCReportType.LOCATION.value,
                        action=s.PCCReportAction.UPDATE.value,
                        pcc_fac_id=facility.facId,
                        name=location_by_name.name,
                        pcc_org_id=organization.orgUuid,
                        use_pcc_backup=True,
                    ).dict()
                )

                logger.info(
                    "Location [{}] update added to approving list. PCC facId: {}",
                    location_by_name.name,
                    facility.facId,
                )

        if objects_to_approve:
            # Save creation report to DB
            report = m.PCCCreationReport(
                data=json.dumps(objects_to_approve),
                company_name=company_name,
                status=m.CreationReportStatus.WAITING,
            )
            report.save()

            logger.info("Creation report {} saved to DB", report.id)


def scan_pcc_activations(scan_record_id: int):
    """
    Generate PCC approving report and set status in scan instance
    after the creation process is finished
    """
    # Get scan record with "IN_PROGRESS" status from DB
    scan_record = m.PCCActivationsScan.query.get(scan_record_id)

    try:
        create_new_creation_reports()
    except Exception as e:
        logger.error("Can't generate new creation report. Reason: {}", e)
        scan_record.status = m.ScanStatus.FAILED
        scan_record.finished_at = datetime.utcnow()
        scan_record.error = str(e)
        scan_record.save()
        raise e

    scan_record.status = m.ScanStatus.SUCCEED
    scan_record.finished_at = datetime.utcnow()
    scan_record.save()
    logger.info("PCC approving report created successfully")
