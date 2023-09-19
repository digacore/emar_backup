from flask import Blueprint, request, abort, render_template, redirect, url_for
from flask_login import login_required, current_user

from app import db, models as m
from app.forms import (
    CompanyMergeSelectForm,
    LocationMergeSelectForm,
)
from app.views.utils import (
    get_companies_merged_locations,
    get_merged_computers_list,
)


merge_blueprint = Blueprint("merge", __name__, url_prefix="/merge")


@merge_blueprint.route("/company/<int:company_id>/first-step", methods=["GET"])
@login_required
def merge_company_first_step(company_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get the primary company
    primary_company = m.Company.query.get_or_404(company_id)

    secondary_company_param = request.args.get("secondary_company", None)
    secondary_company_id = (
        int(secondary_company_param) if secondary_company_param else None
    )
    secondary_company = m.Company.query.get_or_404(secondary_company_id)

    # Prevent from merging company with itself
    if primary_company.id == secondary_company.id:
        abort(400, "You can't merge company with itself.")

    # Create merged lists of locations and computers
    merged_locations = get_companies_merged_locations(
        primary_company, secondary_company
    )
    merged_computers = get_merged_computers_list(primary_company, secondary_company)

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
    merged_computers = get_merged_computers_list(primary_company, secondary_company)
    merge_select_form = CompanyMergeSelectForm(
        request.form, locations=merged_locations, computers=merged_computers
    )

    # Validate the form
    if not merge_select_form.validate_on_submit():
        abort(400, "Invalid form data.")

    selected_locations = [
        m.Location.query.get(location_id)
        for location_id in merge_select_form.merged_locations_list.data
    ]

    selected_computers = [
        m.Computer.query.get(computer_id)
        for computer_id in merge_select_form.merged_computers_list.data
    ]

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
    primary_company.update()

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

    # Add new locations from secondary company to primary company
    for location in selected_locations:
        location.company_name = primary_company.name
        location.update()

    # Delete primary company locations that were not selected
    for location in primary_company.locations:
        if location not in selected_locations:
            db.session.delete(location)
            db.session.commit()

    # Delete secondary company
    db.session.delete(secondary_company)
    db.session.commit()

    return redirect(url_for("company.edit_view", id=primary_company.id))


@merge_blueprint.route("/location/<int:location_id>/first-step", methods=["GET"])
@login_required
def merge_location_first_step(location_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Get the primary and secondary locations
    primary_location = m.Location.query.get_or_404(location_id)

    secondary_company_param = request.args.get("secondary_company", None)
    secondary_location_param = request.args.get("secondary_location", None)
    secondary_location_id = (
        int(secondary_location_param) if secondary_location_param else None
    )
    secondary_location = m.Location.query.get_or_404(secondary_location_id)

    # Prevent from merging company with itself
    if primary_location.id == secondary_location.id:
        abort(400, "You can't merge location with itself.")

    # Create merged list computers
    merged_computers = get_merged_computers_list(primary_location, secondary_location)

    return render_template(
        "merge/location/location-merge-first-step.html",
        primary_location=primary_location,
        secondary_location=secondary_location,
        secondary_company_id=secondary_company_param,
        merged_computers=merged_computers,
    )


@merge_blueprint.route("/location/<int:location_id>/second-step", methods=["POST"])
@login_required
def merge_location_second_step(location_id: int):
    # This page is available only for global-full users
    if current_user.asociated_with.lower() != "global-full":
        abort(403, "You don't have permission to access this page.")

    # Is data confirmed
    is_confirmed_param = request.args.get("confirmed", None)
    is_confirmed = True if is_confirmed_param == "True" else False

    # Get primary and secondary locations
    primary_location = m.Location.query.get_or_404(location_id)

    secondary_company_param = request.args.get("secondary_company", None)
    sec_location_id = request.args.get("secondary_location", None)
    sec_location_id = int(sec_location_id) if sec_location_id else None
    secondary_location = m.Location.query.get_or_404(sec_location_id)

    # Form with selected data
    merged_computers = get_merged_computers_list(primary_location, secondary_location)
    merge_select_form = LocationMergeSelectForm(
        request.form, computers=merged_computers
    )

    selected_computers = [
        m.Computer.query.get(computer_id)
        for computer_id in merge_select_form.merged_computers_list.data
    ]

    # Validate the form
    if not merge_select_form.validate_on_submit():
        abort(400, "Invalid form data.")

    if not is_confirmed:
        return render_template(
            "merge/location/location-merge-second-step.html",
            primary_location=primary_location,
            secondary_location=secondary_location,
            secondary_company_id=secondary_company_param,
            merge_select_form=merge_select_form,
            selected_computers=selected_computers,
        )

    # Merging process
    # Change data of primary company
    # primary_location.name = merge_select_form.name.data
    primary_location.company_name = merge_select_form.company_name.data
    primary_location.default_sftp_path = merge_select_form.default_sftp_path.data
    primary_location.pcc_fac_id = merge_select_form.pcc_fac_id.data
    primary_location.use_pcc_backup = merge_select_form.use_pcc_backup.data
    primary_location.update()

    # Add new computers from secondary to primary location
    for computer in selected_computers:
        computer.location_name = primary_location.name
        computer.company_name = primary_location.company.name
        computer.update()

    # Delete primary location computers that were not selected
    for computer in primary_location.computers:
        if computer not in selected_computers:
            db.session.delete(computer)
            db.session.commit()

    # Delete secondary location
    db.session.delete(secondary_location)
    db.session.commit()

    return redirect(
        url_for(
            "merge.merge_company_first_step",
            company_id=primary_location.company.id,
            secondary_company=secondary_company_param,
        )
    )
