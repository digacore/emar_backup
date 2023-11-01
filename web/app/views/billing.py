from datetime import datetime, timedelta

from sqlalchemy.orm import Query
from flask import render_template, Blueprint, abort, request
from flask_login import login_required, current_user

from app import models as m, db
from app.controllers import create_pagination

from config import BaseConfig as CFG


billing_blueprint = Blueprint("billing", __name__, url_prefix="/billing")


@billing_blueprint.route("/", methods=["GET"])
@login_required
def get_billing_page():
    # This page is available only for Global users
    if current_user.permission != m.UserPermissionLevel.GLOBAL:
        abort(403, "You don't have permission to access this page.")

    q: str | None = request.args.get("q", type=str, default=None)
    per_page: int = request.args.get("per_page", 25, type=int)

    # Default start time is 30 days ago (from today - EST timezone)
    default_start_time: datetime = CFG.offset_to_est(datetime.utcnow(), True).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=30)
    from_date: datetime = request.args.get(
        "from_date",
        default=default_start_time,
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d"),
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
        type=lambda date_string: datetime.strptime(date_string, "%Y-%m-%d"),
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

    return render_template(
        "billing-page.html",
        page=pagination,
        companies=companies,
        from_date=from_date,
        to_date=to_date,
        max_date=default_end_time,
    )
