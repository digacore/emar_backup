from flask import render_template, Blueprint, request, abort, redirect, url_for
from flask_login import login_required, current_user

from app import models as m, db
from app.controllers import create_pagination

from worker import create_new_pcc_orgs_facs_task

from app.logger import logger


pcc_blueprint = Blueprint("pcc", __name__, url_prefix="/pcc")


@pcc_blueprint.route("/creation-report", methods=["GET", "POST"])
@login_required
def creation_report():
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # If POST, create new report with status "IN_PROGRESS" and run celery task
    if request.method == "POST":
        scan_record = m.PCCActivationsScan(status=m.ScanStatus.IN_PROGRESS)
        scan_record.save()

        create_new_pcc_orgs_facs_task.delay(scan_record.id)
        logger.debug("Celery task for PCC orgs and facs creation started")

        return redirect(url_for("pcc.creation_report"))

    # Paginated reports
    per_page = request.args.get("per_page", 25, type=int)

    reports_query = m.PCCCreationReport.query
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
        current_scan_status = "READY"
    # Second scanning
    elif len(all_scan_records) == 1:
        if all_scan_records[0].status == m.ScanStatus.IN_PROGRESS:
            previous_scan_result = "-"
            current_scan_status = all_scan_records[0].status.value
        else:
            previous_scan_result = all_scan_records[0].status.value
            current_scan_status = "READY"
    # Third and more scanning
    else:
        if all_scan_records[0].status == m.ScanStatus.IN_PROGRESS:
            previous_scan_result = all_scan_records[1].status.value
            current_scan_status = all_scan_records[0].status.value
        else:
            previous_scan_result = all_scan_records[0].status.value
            current_scan_status = "READY"

    return render_template(
        "pcc/creation_report.html",
        reports=reports,
        page=pagination,
        previous_scan_result=previous_scan_result,
        current_scan_status=current_scan_status,
    )
