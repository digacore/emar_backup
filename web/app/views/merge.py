from flask import Blueprint, request, abort, render_template
from flask_login import login_required, current_user

from app import models as m
from app.forms import CompanyMergeFirstStepForm, CompanyMergeSelectForm
from app.views.utils import (
    get_companies_merged_locations,
    get_companies_merged_computers,
)


merge_blueprint = Blueprint("merge", __name__, url_prefix="/merge")


@merge_blueprint.route("/company/<int:company_id>/first-step", methods=["POST"])
@login_required
def merge_company_first_step(company_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get the primary company
    primary_company = m.Company.query.get_or_404(company_id)

    merge_start_form = CompanyMergeFirstStepForm(request.form)

    # Validate the form
    if not merge_start_form.validate_on_submit():
        abort(400, "Invalid form data.")

    secondary_company = m.Company.query.filter_by(
        name=merge_start_form.secondary_company.data
    ).first()

    if not secondary_company:
        abort(404, "Secondary company not found.")

    # Create merged lists of locations and computers
    merged_locations = get_companies_merged_locations(
        primary_company, secondary_company
    )
    merged_computers = get_companies_merged_computers(
        primary_company, secondary_company
    )

    return render_template(
        "merge/company/company-merge-first-step.html",
        primary_company=primary_company,
        secondary_company=secondary_company,
        merged_locations=merged_locations,
        merged_computers=merged_computers,
    )


@merge_blueprint.route("/company/<int:company_id>/second-step", methods=["POST"])
@login_required
def merge_company_second_step(company_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get primary company and secondary companies
    primary_company = m.Company.query.get_or_404(company_id)

    sec_comp_id = request.args.get("secondary_company", None)
    sec_comp_id = int(sec_comp_id) if sec_comp_id else None
    secondary_company = m.Company.query.get_or_404(sec_comp_id)

    # Form with selected data
    merged_locations = get_companies_merged_locations(
        primary_company, secondary_company
    )
    merged_computers = get_companies_merged_computers(
        primary_company, secondary_company
    )
    merge_select_form = CompanyMergeSelectForm(
        request.form, locations=merged_locations, computers=merged_computers
    )

    # Validate the form
    if not merge_select_form.validate_on_submit():
        abort(400, "Invalid form data.")

    return render_template(
        "merge/company/company-merge-second-step.html",
        primary_company=primary_company,
        secondary_company=secondary_company,
        merge_select_form=merge_select_form,
    )
