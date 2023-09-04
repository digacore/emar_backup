from flask import render_template, Blueprint, request, abort, redirect, url_for
from flask_login import login_required, current_user

from app import models as m, db
from app.controllers import create_pagination

from worker import scan_pcc_activations

from app.logger import logger


pcc_blueprint = Blueprint("pcc", __name__, url_prefix="/pcc")


@pcc_blueprint.route("/scan-activations", methods=["GET", "POST"])
@login_required
def scan_activations():
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # If POST, create new report with status "IN_PROGRESS" and run celery task
    if request.method == "POST":
        scan_record = m.PCCActivationsScan(status=m.ScanStatus.IN_PROGRESS)
        scan_record.save()

        scan_pcc_activations.delay(scan_record.id)
        logger.debug("Celery task for PCC activations scanning started")

        return redirect(url_for("pcc.scan_activations"))

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
        if q:
            reports_query = reports_query.filter(
                (m.PCCCreationReport.company_name.ilike(f"%{q}%"))
                # | (m.PCCCreationReport.data.ilike(f"%{q}%"))
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
                # | (m.PCCCreationReport.data.ilike(f"%{q}%"))
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

    return render_template(
        "pcc/scan_activations.html",
        reports=reports,
        page=pagination,
        previous_scan_result=previous_scan_result,
        previous_scan_finished_at=previous_scan_finished_at,
        current_scan_status=current_scan_status,
        approved_page=approved_page,
    )
