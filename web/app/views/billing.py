from flask import render_template, Blueprint, abort
from flask_login import login_required, current_user

from app import models as m


billing_blueprint = Blueprint("billing", __name__, url_prefix="/billing")


@billing_blueprint.route("/", methods=["GET"])
@login_required
def get_billing_page():
    # This page is available only for Global users
    if current_user.permission != m.UserPermissionLevel.GLOBAL:
        abort(403, "You don't have permission to access this page.")

    # Retrieve all companies
    companies = m.Company.query.filter(m.Company.is_global.is_(False)).all()

    return render_template(
        "billing-page.html",
        companies=companies,
    )
