import io
import enum
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from sqlalchemy.orm import Query
from flask import render_template, Blueprint, abort, request, send_file
from flask_login import login_required, current_user

from app import models as m, db
from app.controllers import create_pagination, create_general_billing_report
from app.logger import logger

from config import BaseConfig as CFG


billing_blueprint = Blueprint("billing", __name__, url_prefix="/billing")


class FixedTimeRangeType(enum.Enum):
    """Fixed time ranges for billing report"""

    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    THIS_MONTH = "THIS_MONTH"
    THIS_YEAR = "THIS_YEAR"
    CUSTOM = "CUSTOM"


@billing_blueprint.route("/", methods=["GET"])
@login_required
def get_billing_page():
    # This page is available only for Global users
    if current_user.permission != m.UserPermissionLevel.GLOBAL:
        abort(403, "You don't have permission to access this page.")

    q: str | None = request.args.get("q", type=str, default=None)
    per_page: int = request.args.get("per_page", 25, type=int)

    # Default start time is start of current month at 00:00 (EST timezone).
    default_start_time: datetime = CFG.offset_to_est(datetime.utcnow(), True).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    from_date: datetime = request.args.get(
        "from_date",
        default=default_start_time,
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        ),
    )

    # Default end time is today at 00:00 (EST timezone).
    # This is because we don't want to include today's data in the report.
    # Default end time is also max date parameter for datepicker.
    default_end_time: datetime = CFG.offset_to_est(datetime.utcnow(), True).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    to_date: datetime = request.args.get(
        "to_date",
        default=default_end_time,
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        ),
    )

    # Companies query
    companies_query: Query = m.Company.query.filter(m.Company.is_global.is_(False))

    # Filter query by search query
    if q:
        companies_query = companies_query.filter((m.Company.name.ilike(f"%{q}%")))

    # Pagination
    pagination = create_pagination(total=m.count(companies_query), page_size=per_page)

    companies: list[m.Company] = (
        db.session.execute(
            companies_query.order_by(m.Company.name)
            .limit(pagination.per_page)
            .offset(pagination.skip)
        )
        .scalars()
        .all()
    )

    # Determine fixed time range type
    current_duration: timedelta = to_date - from_date
    if current_duration == timedelta(days=7):
        fixed_time_range_type = FixedTimeRangeType.LAST_7_DAYS.value
    elif current_duration == timedelta(days=30):
        fixed_time_range_type = FixedTimeRangeType.LAST_30_DAYS.value
    elif from_date == default_start_time and to_date == default_end_time:
        fixed_time_range_type = FixedTimeRangeType.THIS_MONTH.value
    elif (
        from_date
        == datetime(
            year=from_date.year, month=1, day=1, tzinfo=ZoneInfo("America/New_York")
        )
        and to_date == default_end_time
    ):
        fixed_time_range_type = FixedTimeRangeType.THIS_YEAR.value
    else:
        fixed_time_range_type = FixedTimeRangeType.CUSTOM.value

    return render_template(
        "billing-page.html",
        page=pagination,
        companies=companies,
        from_date=from_date,
        to_date=to_date,
        max_date=default_end_time,
        fixed_time_range_type=fixed_time_range_type,
    )


@billing_blueprint.route("/report", methods=["GET"])
@login_required
def general_billing_report():
    """Generates general billing report for all the companies and returns it as .xlsx file

    Returns:
        Response: billing report as .xlsx file
    """
    # Only global users can access this information
    if current_user.permission != m.UserPermissionLevel.GLOBAL:
        logger.error(
            f"User {current_user.username} tried to generate general billing report"
        )
        abort(403, "You don't have access to this information.")

    # We recognize these dates as EST timezone
    from_date: datetime | None = request.args.get(
        "from_date",
        default=None,
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        ),
    )
    to_date: datetime | None = request.args.get(
        "to_date",
        default=None,
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/New_York")
        ),
    )

    if not from_date or not to_date:
        logger.error("Incorrect date format to generate general billing report")
        abort(400, "Invalid date format.")

    # Generate general billing report for company
    report: io.BytesIO = create_general_billing_report(from_date, to_date)

    return send_file(
        report,
        mimetype="application/ms-excel",
        as_attachment=True,
        download_name="General_Report.xlsx",
    )
