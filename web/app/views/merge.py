from flask import Blueprint, request, abort, render_template
from flask_login import login_required, current_user

from app import models as m
from app.forms import MergeFirstStepForm


merge_blueprint = Blueprint("merge", __name__, url_prefix="/merge")


@merge_blueprint.route("/company/<int:company_id>/first-step", methods=["POST"])
@login_required
def merge_company_first_step(company_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get the primary company
    primary_company = m.Company.query.get_or_404(company_id)

    merge_start_form = MergeFirstStepForm(request.form)

    # Validate the form
    if not merge_start_form.validate_on_submit():
        abort(400, "Invalid form data.")

    secondary_company = m.Company.query.filter_by(
        name=merge_start_form.secondary_company.data
    ).first()

    if not secondary_company:
        abort(404, "Secondary company not found.")

    # Create merged lists of locations and computers
    primary_company_locations = primary_company.locations
    primary_company_computers = primary_company.computers

    secondary_company_locations = secondary_company.locations
    secondary_company_computers = secondary_company.computers

    merged_locations = primary_company_locations
    for location in secondary_company_locations:
        if location not in merged_locations:
            merged_locations.append(location)

    merged_computers = primary_company_computers
    for computer in secondary_company_computers:
        if computer not in merged_computers:
            merged_computers.append(computer)

    return render_template(
        "merge.html",
        primary_company=primary_company,
        secondary_company=secondary_company,
        merged_locations=merged_locations,
        merged_computers=merged_computers,
    )
