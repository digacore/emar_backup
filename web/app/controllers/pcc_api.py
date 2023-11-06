import os
import json
import time
import requests
from requests.exceptions import HTTPError
from urllib.parse import urljoin
from datetime import datetime, timedelta
from pydantic import ValidationError

from flask import current_app, abort

from app.logger import logger
from app import models as m, schema as s
from app.utils import get_base64_string
from config import BaseConfig as CFG


class UnknownTypeError(Exception):
    pass


class SpikeArrestError(Exception):
    pass


def update_daily_requests_count(reset_time: int, remaining_requests: int) -> None:
    """Update daily requests count

    Args:
        reset_time (int): epoch reset time in milliseconds
        remaining_requests (int): remaining requests count
    """
    # Convert epoch time to datetime
    reset_time_as_date: datetime = datetime.utcfromtimestamp(reset_time / 1000)

    used_requests = current_app.config["PCC_DAILY_QUOTA_LIMIT"] - remaining_requests

    # Check if reset time is already exists
    daily_requests: m.PCCDailyRequest | None = m.PCCDailyRequest.query.filter_by(
        reset_time=reset_time_as_date
    ).first()

    # If not - create new
    if not daily_requests:
        daily_requests = m.PCCDailyRequest(
            reset_time=reset_time_as_date, requests_count=used_requests
        )
        daily_requests.save()
    # If exists - update
    else:
        daily_requests.requests_count = used_requests
        daily_requests.update()


def check_daily_requests_count() -> None:
    """
    Check daily requests count and raise error if it's exceeded
    """
    # Get the valid requests count for current time
    current_requests_number: m.PCCDailyRequest | None = m.PCCDailyRequest.query.filter(
        m.PCCDailyRequest.reset_time > datetime.utcnow()
    ).first()

    # If there is no suitable counter for current time - skip
    if (
        not current_requests_number
        or current_requests_number.requests_count
        < current_app.config["PCC_DAILY_QUOTA_LIMIT"]
    ):
        return True

    # If requests count is exceeded - raise error
    if (
        current_requests_number.requests_count
        >= current_app.config["PCC_DAILY_QUOTA_LIMIT"]
    ):
        logger.error(
            "Daily requests limit exceeded [{}]. Current requests count: {}",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            current_requests_number.requests_count,
        )
        abort(
            429,
            f"Daily requests limit exceeded. Current requests count: {current_requests_number.requests_count}",
        )


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
        response.raise_for_status()

        access_token_info = s.TwoLeggedAuthResult.parse_obj(response.json())
    except (ValidationError, HTTPError) as e:
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


def execute_pcc_request(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    stream: bool | None = None,
):
    """Execute PCC API request and handle all necessary errors

    Args:
        url (str): pcc api url
        params (dict): query params
        headers (dict): request headers

    Raises:
        SpikeArrestError: SpikeArrest error (minute quota)

    Returns:
        Response: response object
    """
    # Two retries for the case when we have SpikeArrest error (frequency 20 ms)
    for i in range(2):
        # Check daily requests count and raise error if it's exceeded
        check_daily_requests_count()
        try:
            res = requests.get(
                url,
                params=params,
                headers=headers,
                stream=stream,
                cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
            )

            if res.headers.get("X-Quota-Time-To-Reset") and res.headers.get(
                "X-Quota-Remaining"
            ):
                logger.debug(
                    "Daily Quota limit: {}. Requests remains: {}",
                    int(res.headers["X-Quota-Limit"]),
                    int(res.headers["X-Quota-Remaining"]),
                )

                update_daily_requests_count(
                    int(res.headers["X-Quota-Time-To-Reset"]),
                    int(res.headers["X-Quota-Remaining"]),
                )

            if res.status_code in (429, 503):
                # When we have SpikeArrest error because of minute quota - raise exception
                if res.headers["X-Quota-Minute-Remaining"] == 0:
                    raise SpikeArrestError(
                        "SpikeArrest error (minute quota). Retry in 1 minute"
                    )
                # When we have SpikeArrest error because of frequency (20 ms)
                else:
                    # If that is first time - retry after 400 ms
                    if i == 0:
                        time.sleep(0.4)
                        continue
                    else:
                        raise SpikeArrestError(
                            "SpikeArrest error (too high frequency of requests)"
                        )

            res.raise_for_status()
        except (SpikeArrestError, HTTPError) as e:
            logger.error(str(e))
            raise e

        return res


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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    page = 1

    while should_download:
        params = {"page": page, "page_size": 200}
        res = execute_pcc_request(url, params, headers)

        try:
            parsed_res = s.ActivationsResponse.parse_obj(res.json())
        except ValidationError as e:
            logger.error(
                "Error in validation of app activations response. Reason: {}", e
            )
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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    page = 1

    while should_download:
        params = {"page": page, "page_size": 200}
        res = execute_pcc_request(url, params, headers)

        try:
            parsed_res = s.FacilitiesListResponse.parse_obj(res.json())
        except ValidationError as e:
            logger.error(
                "Error in validation of facilities list response. Reason: {}", e
            )
            raise e

        facilities_list.extend(parsed_res.data)
        page += 1
        should_download = parsed_res.paging.hasMore

    return facilities_list


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

        facilities_list = get_org_facilities_list(organization.orgUuid)

        # If not all the company facilities are integrated to our app - filter them
        if organization.scope != 1:
            activated_facilities: list[s.Facility] = []
            for facility in facilities_list:
                for activated_facility in organization.facilityInfo:
                    if facility.facId == activated_facility.facId:
                        activated_facilities.append(facility)
                        break

            facilities_list = activated_facilities

        match type(facilities_list[0]):
            case s.Facility:
                company_name = facilities_list[0].orgName

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
