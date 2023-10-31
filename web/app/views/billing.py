from flask import render_template, Blueprint, abort, request
from flask_login import login_required, current_user

from app import models as m, db
from app.controllers import create_pagination


billing_blueprint = Blueprint("billing", __name__, url_prefix="/billing")


@billing_blueprint.route("/", methods=["GET"])
@login_required
def get_billing_page():
    # This page is available only for Global users
    if current_user.permission != m.UserPermissionLevel.GLOBAL:
        abort(403, "You don't have permission to access this page.")

    q = request.args.get("q", type=str, default=None)
    per_page = request.args.get("per_page", 25, type=int)

    # Companies query
    companies_query = m.Company.query.filter(m.Company.is_global.is_(False))

    # Filter query by search query
    if q:
        companies_query = companies_query.filter((m.Company.name.ilike(f"%{q}%")))

    # Pagination
    pagination = create_pagination(total=m.count(companies_query), page_size=per_page)

    companies = (
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
    )
