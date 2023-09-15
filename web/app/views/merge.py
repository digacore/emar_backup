from flask import Blueprint, request, abort, render_template, redirect, url_for
from flask_login import login_required, current_user

from app import db, models as m
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

    is_confirmed_param = request.args.get("confirmed", None)
    is_confirmed = True if is_confirmed_param == "True" else False

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

    selected_locations = [
        m.Location.query.get(location_id)
        for location_id in merge_select_form.merged_locations_list.data
    ]

    selected_computers = [
        m.Computer.query.get(computer_id)
        for computer_id in merge_select_form.merged_computers_list.data
    ]

    # Validate the form
    if not merge_select_form.validate_on_submit():
        abort(400, "Invalid form data.")

    if not is_confirmed:
        return render_template(
            "merge/company/company-merge-second-step.html",
            primary_company=primary_company,
            secondary_company=secondary_company,
            merge_select_form=merge_select_form,
            selected_locations=selected_locations,
            selected_computers=selected_computers,
        )

    # Merging process
    # Change data of primary company
    # primary_company.name = reviewed_form.name.data
    primary_company.default_sftp_username = merge_select_form.default_sftp_username.data
    primary_company.default_sftp_password = merge_select_form.default_sftp_password.data
    primary_company.pcc_org_id = merge_select_form.pcc_org_id.data

    # Add new computers from secondary company to primary company
    for computer in selected_computers:
        computer.company_name = primary_company.name
        computer.update()

        # If location is not selected, remove it from computer
        if computer.location not in selected_locations:
            computer.location_name = None
            computer.update()

    # Delete primary company computers that were not selected
    for computer in primary_company.computers:
        if computer not in selected_computers:
            db.session.delete(computer)
            db.session.commit()

    # Delete secondary company computers that were not selected
    for computer in secondary_company.computers:
        if computer not in selected_computers:
            db.session.delete(computer)
            db.session.commit()

    # Add new locations from secondary company to primary company
    for location in selected_locations:
        location.company_name = primary_company.name
        location.update()

    # Delete primary company locations that were not selected
    for location in primary_company.locations:
        if location not in selected_locations:
            db.session.delete(location)
            db.session.commit()

    # Delete secondary company locations that were not selected
    for location in secondary_company.locations:
        if location not in selected_locations:
            db.session.delete(location)
            db.session.commit()

    # Delete secondary company
    db.session.delete(secondary_company)
    db.session.commit()

    return redirect(url_for("company.edit_view", id=primary_company.id))
