import os
import json
import requests
from datetime import datetime
from urllib.parse import urljoin
from flask import Response, abort
from flask_jwt_extended import jwt_required

from app import schema as s, models as m
from app.views.blueprint import BlueprintApi
from app.controllers import get_pcc_2_legged_token, create_system_log
from app.logger import logger
from config import BaseConfig as CFG


pcc_api_blueprint = BlueprintApi("pcc_api", __name__, url_prefix="/pcc_api")


@pcc_api_blueprint.post("/download_backup")
def download_backup_from_pcc(body: s.GetCredentials) -> Response:
    # Find computer in DB
    computer: m.Computer = (
        m.Computer.query.filter_by(
            identifier_key=body.identifier_key, computer_name=body.computer_name
        ).first()
        if body.identifier_key and body.computer_name
        else None
    )

    if not computer:
        abort(
            404,
            f"Computer with such credentials not found. Computer_name: \
                {body.computer_name}, identifier_key: {body.identifier_key}",
        )

    # Check that pcc_org_id and pcc_fac_id are present
    if not computer.company.pcc_org_id or not computer.location.pcc_fac_id:
        logger.error(
            "Can't download backup for computer {}. PCC_ORG_ID or PCC_FAC_ID is not set",
            computer,
        )
        abort(409, "PCC_ORG_ID or PCC_FAC_ID is not set")

    # Get 2-legged access token
    token = get_pcc_2_legged_token()

    # Download backup file
    backup_route = os.path.join(
        "api",
        "public",
        "preview1",
        "orgs",
        computer.company.pcc_org_id,
        "facs",
        str(computer.location.pcc_fac_id),
        "backup-files",
    )
    url = urljoin(CFG.PCC_BASE_URL, backup_route)
    try:
        res = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
            stream=True,
        )
    except Exception as e:
        logger.error(
            "Can't download backup from PCC API for computer {}. Reason: {}",
            computer.computer_name,
            e,
        )
        raise e

    return Response(
        res.iter_content(chunk_size=10 * 1024),
        content_type=res.headers["Content-Type"],
        headers={"Content-Disposition": "attachment; filename=emar_backup.zip"},
    )


@pcc_api_blueprint.patch("/creation-report/<int:report_id>")
@jwt_required()
def creation_report(
    body: s.PartialCreationReport, path: s.CreationReportAPIPath
) -> Response:
    # Find report in DB
    report = m.PCCCreationReport.query.get(path.report_id)
    if not report:
        abort(404, f"Report with id {path.report_id} not found")

    # Update report data field
    if body.data:
        report.data = json.dumps(body.data)
        report.update()

    # Update report status
    if body.status:
        # If status is "REJECTED" just change it
        if body.status == "REJECTED":
            report.status = body.status
            report.update()

        # If status is "APPROVED" we need to create new company and locations
        elif body.status == "APPROVED":
            # Create company if it doesn't exist or update if it doesn't have pcc_org_id
            parsed_data = json.loads(report.data)
            objects_to_create = [
                s.PCCReportObject.parse_obj(obj) for obj in parsed_data
            ]

            created_objects = []

            # Find object with company creation or update
            company_obj = None
            for obj in objects_to_create:
                if obj.type == "Company":
                    company_obj = obj
                    break

            # If company_obj is None, it means that company already exists and we can find it by name
            if not company_obj:
                company = m.Company.query.filter_by(name=report.company_name).first()
            else:
                # Create the new company
                if company_obj.action == "Create":
                    company = m.Company(
                        name=company_obj.name, pcc_org_id=company_obj.pcc_org_id
                    )
                    company.save()
                    create_system_log(m.SystemLogType.COMPANY_CREATED, company, None)

                    new_company_obj = s.PCCReportObject(
                        id=company.id,
                        type="Company",
                        name=company.name,
                        action="Create",
                        pcc_org_id=company.pcc_org_id,
                    )

                    created_objects.append(new_company_obj.dict())

                # Update the existing company
                elif company_obj.action == "Update":
                    company = m.Company.query.filter_by(name=company_obj.name).first()
                    company.pcc_org_id = company_obj.pcc_org_id
                    company.update()
                    create_system_log(m.SystemLogType.COMPANY_UPDATED, company, None)

                    new_company_obj = s.PCCReportObject(
                        id=company.id,
                        type="Company",
                        name=company.name,
                        action="Update",
                        pcc_org_id=company.pcc_org_id,
                    )

                    created_objects.append(new_company_obj.dict())

            # Create and update locations
            for obj in objects_to_create:
                if obj.type != "Location":
                    continue

                # Create the new location
                if obj.action == "Create":
                    location = m.Location(
                        name=obj.name,
                        company_name=company.name,
                        pcc_fac_id=obj.pcc_fac_id,
                        use_pcc_backup=bool(obj.use_pcc_backup),
                    )
                    location.save()
                    create_system_log(m.SystemLogType.LOCATION_CREATED, location, None)

                    new_obj = s.PCCReportObject(
                        id=location.id,
                        type="Location",
                        name=location.name,
                        action="Create",
                        pcc_fac_id=location.pcc_fac_id,
                        use_pcc_backup=location.use_pcc_backup,
                    )

                    created_objects.append(new_obj.dict())

                # Update the existing location
                elif obj.action == "Update":
                    location = m.Location.query.filter(
                        m.Location.name == obj.name,
                        m.Location.company_name == company.name,
                    ).first()
                    location.pcc_fac_id = obj.pcc_fac_id
                    location.use_pcc_backup = bool(obj.use_pcc_backup)
                    location.update()
                    create_system_log(m.SystemLogType.LOCATION_UPDATED, location, None)

                    new_obj = s.PCCReportObject(
                        id=location.id,
                        type="Location",
                        name=location.name,
                        action="Update",
                        pcc_fac_id=location.pcc_fac_id,
                        use_pcc_backup=location.use_pcc_backup,
                    )

                    created_objects.append(new_obj.dict())

            # Update report
            report.status = body.status
            report.data = json.dumps(created_objects)
            report.company_id = company.id
            report.status_changed_at = datetime.utcnow()
            report.update()

    return Response(status=200)
