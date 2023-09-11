import json
from datetime import datetime

from flask import (
    render_template,
    Blueprint,
    request,
    abort,
    redirect,
    url_for,
    Response,
)
from flask_login import login_required, current_user
from sqlalchemy import cast, String

from app import db, models as m, schema as s
from app.controllers import create_pagination, create_system_log

from worker import scan_pcc_activations

from app.logger import logger


pcc_blueprint = Blueprint("pcc", __name__, url_prefix="/pcc")


@pcc_blueprint.route("/creation-reports", methods=["GET", "POST"])
@login_required
def creation_reports():
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # If POST, create new report with status "IN_PROGRESS" and run celery task
    if request.method == "POST":
        waiting_creation_report = m.PCCCreationReport.query.filter_by(
            status=m.CreationReportStatus.WAITING
        ).first()

        if waiting_creation_report:
            abort(409, "There is already a report with status WAITING")

        scan_record = m.PCCActivationsScan(status=m.ScanStatus.IN_PROGRESS)
        scan_record.save()

        scan_pcc_activations.delay(scan_record.id)
        logger.debug("Celery task for PCC activations scanning started")

        return redirect(url_for("pcc.creation_reports"))

    # Paginated reports or waiting for approve objects
    approved_page = request.args.get(
        "approved_page", False, type=lambda v: v.lower() == "true"
    )
    per_page = request.args.get("per_page", 25, type=int)
    q = request.args.get("q", type=str, default=None)

    if not approved_page:
        reports_query = m.PCCCreationReport.query.filter_by(
            status=m.CreationReportStatus.WAITING
        )

        # Filter query by search query
        # NOTE: search over the JSON field converted to string by substring is not the best idea
        if q:
            reports_query = reports_query.filter(
                (m.PCCCreationReport.company_name.ilike(f"%{q}%"))
                | cast(m.PCCCreationReport.data, String).ilike(f"%{q}%")
            )

        pagination = create_pagination(total=m.count(reports_query), page_size=per_page)

        # Current page of reports that will be used for table
        reports = (
            db.session.execute(
                reports_query.order_by(m.PCCCreationReport.created_at.desc())
                .limit(pagination.per_page)
                .offset(pagination.skip)
            )
            .scalars()
            .all()
        )
    else:
        reports_query = m.PCCCreationReport.query.filter(
            (m.PCCCreationReport.status == m.CreationReportStatus.APPROVED)
            | (m.PCCCreationReport.status == m.CreationReportStatus.REJECTED)
        )

        # Filter query by search query
        if q:
            reports_query = reports_query.filter(
                (m.PCCCreationReport.company_name.ilike(f"%{q}%"))
                | cast(m.PCCCreationReport.data, String).ilike(f"%{q}%")
            )

        pagination = create_pagination(total=m.count(reports_query), page_size=per_page)

        # Current page of reports that will be used for table
        reports = (
            db.session.execute(
                reports_query.order_by(m.PCCCreationReport.created_at.desc())
                .limit(pagination.per_page)
                .offset(pagination.skip)
            )
            .scalars()
            .all()
        )

    # Results of previous scanning and current status
    all_scan_records = m.PCCActivationsScan.query.order_by(
        m.PCCActivationsScan.created_at.desc()
    ).all()

    # The first scanning
    if len(all_scan_records) == 0:
        previous_scan_result = "-"
        previous_scan_finished_at = "-"
        current_scan_status = "READY"
    # Second scanning
    elif len(all_scan_records) == 1:
        if all_scan_records[0].status == m.ScanStatus.IN_PROGRESS:
            previous_scan_result = "-"
            previous_scan_finished_at = "-"
            current_scan_status = all_scan_records[0].status.value
        else:
            previous_scan_result = all_scan_records[0].status.value
            previous_scan_finished_at = all_scan_records[0].finished_at
            current_scan_status = "READY"
    # Third and more scanning
    else:
        if all_scan_records[0].status == m.ScanStatus.IN_PROGRESS:
            previous_scan_result = all_scan_records[1].status.value
            previous_scan_finished_at = all_scan_records[1].finished_at
            current_scan_status = all_scan_records[0].status.value
        else:
            previous_scan_result = all_scan_records[0].status.value
            previous_scan_finished_at = all_scan_records[0].finished_at
            current_scan_status = "READY"

    # Check if the scanning button should be enabled or disabled
    waiting_creation_report = m.PCCCreationReport.query.filter_by(
        status=m.CreationReportStatus.WAITING
    ).first()

    if current_scan_status == "READY" and not waiting_creation_report:
        scan_disabled = False
        reason = ""
    else:
        scan_disabled = True
        reason = (
            "Current scanning is in progress"
            if current_scan_status == m.ScanStatus.IN_PROGRESS.value
            else "Approve or reject the waiting reports"
        )

    return render_template(
        "pcc/creation-reports.html",
        reports=reports,
        page=pagination,
        previous_scan_result=previous_scan_result,
        previous_scan_finished_at=previous_scan_finished_at,
        current_scan_status=current_scan_status,
        approved_page=approved_page,
        scan_disabled=scan_disabled,
        reason=reason,
    )


@pcc_blueprint.route("/creation-reports/<int:report_id>", methods=["GET", "POST"])
@login_required
def get_creation_report(report_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Query params
    status = request.args.get("status", type=str, default=None)
    report = m.PCCCreationReport.query.get(report_id)

    if not report:
        abort(404, f"Report with id {report_id} not found")

    # TODO: validation through the Flask form
    # validate_on_submit()
    if request.method == "POST":
        new_data = request.form.get("data", type=str, default=None)
        if new_data:
            report.data = new_data
            report.update()

        return Response(status=200)

    elif request.method == "GET":
        # If status is "REJECTED" just change it
        if status == "REJECTED":
            report.status = m.CreationReportStatus.REJECTED
            report.update()

        # If status is "APPROVED" we need to create new company and locations
        elif status == "APPROVED":
            # Create company if it doesn't exist or update if it doesn't have pcc_org_id
            parsed_data = json.loads(report.data)
            objects_to_create = [
                s.PCCReportObject.parse_obj(obj) for obj in parsed_data
            ]

            created_objects = []

            # Find object with company creation or update
            company_obj = None
            for obj in objects_to_create:
                if obj.type == s.PCCReportType.COMPANY.value:
                    company_obj = obj
                    break

            # If company_obj is None, it means that company already exists and we can find it by name
            if not company_obj:
                company = m.Company.query.filter_by(name=report.company_name).first()
            else:
                # Create the new company
                if company_obj.action == s.PCCReportAction.CREATE.value:
                    company = m.Company(
                        name=company_obj.name,
                        pcc_org_id=company_obj.pcc_org_id,
                        created_from_pcc=True,
                    )
                    company.save()
                    create_system_log(m.SystemLogType.COMPANY_CREATED, company, None)

                    new_company_obj = s.PCCReportObject(
                        id=company.id,
                        type=s.PCCReportType.COMPANY.value,
                        name=company.name,
                        action=s.PCCReportAction.CREATE.value,
                        pcc_org_id=company.pcc_org_id,
                    )

                    created_objects.append(new_company_obj.dict())

                # Update the existing company
                elif company_obj.action == s.PCCReportAction.UPDATE.value:
                    company = m.Company.query.filter_by(name=company_obj.name).first()
                    company.pcc_org_id = company_obj.pcc_org_id
                    company.update()
                    create_system_log(m.SystemLogType.COMPANY_UPDATED, company, None)

                    new_company_obj = s.PCCReportObject(
                        id=company.id,
                        type=s.PCCReportType.COMPANY.value,
                        name=company.name,
                        action=s.PCCReportAction.UPDATE.value,
                        pcc_org_id=company.pcc_org_id,
                    )

                    created_objects.append(new_company_obj.dict())

            # Create and update locations
            for obj in objects_to_create:
                if obj.type != s.PCCReportType.LOCATION.value:
                    continue

                # Create the new location
                if obj.action == s.PCCReportAction.CREATE.value:
                    location = m.Location(
                        name=obj.name,
                        company_name=company.name,
                        pcc_fac_id=obj.pcc_fac_id,
                        use_pcc_backup=bool(obj.use_pcc_backup),
                        created_from_pcc=True,
                    )
                    location.save()
                    create_system_log(m.SystemLogType.LOCATION_CREATED, location, None)

                    new_obj = s.PCCReportObject(
                        id=location.id,
                        type=s.PCCReportType.LOCATION.value,
                        name=location.name,
                        action=s.PCCReportAction.CREATE.value,
                        pcc_fac_id=location.pcc_fac_id,
                        use_pcc_backup=location.use_pcc_backup,
                    )

                    created_objects.append(new_obj.dict())

                # Update the existing location
                elif obj.action == s.PCCReportAction.UPDATE.value:
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
                        type=s.PCCReportType.LOCATION.value,
                        name=location.name,
                        action=s.PCCReportAction.UPDATE.value,
                        pcc_fac_id=location.pcc_fac_id,
                        use_pcc_backup=location.use_pcc_backup,
                    )

                    created_objects.append(new_obj.dict())

            # Update report
            report.status = m.CreationReportStatus.APPROVED
            report.data = json.dumps(created_objects)
            report.company_id = company.id
            report.status_changed_at = datetime.utcnow()
            report.update()

        return redirect(url_for("pcc.creation_reports"))
