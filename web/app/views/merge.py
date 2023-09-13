from flask import Blueprint, request, abort, render_template
from flask_login import login_required, current_user

from app import models as m
from app.forms import MergeSecondaryCompany


merge_blueprint = Blueprint("merge", __name__, url_prefix="/merge")


@merge_blueprint.route("/company/<int:company_id>", methods=["POST"])
@login_required
def merge_company(company_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get the primary company
    primary_company = m.Company.query.get_or_404(company_id)

    form = MergeSecondaryCompany(request.form)

    if form.validate_on_submit():
        return render_template(
            "merge.html",
            company1=primary_company.name,
            company2=form.secondary_company.data,
        )
