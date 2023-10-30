from flask import jsonify, Blueprint, abort, request
from flask_login import login_required, current_user

from app import models as m

from app.logger import logger

from .utils import has_access_to_company


company_blueprint = Blueprint("company_blueprint", __name__, url_prefix="/company")


@company_blueprint.route("/<int:company_id>/sftp_data", methods=["GET"])
@login_required
def company_sftp_data(company_id: int):
    """Returns company sftp data as JSON

    Args:
        company_id (int): company id

    Returns:
        JSON: company sftp data
    """
    company: m.Company = m.Company.query.get_or_404(company_id)

    # Check if user has access to company information
    if not has_access_to_company(current_user, company):
        logger.error(
            "User [{}] with access level [{}] tried to access company [{}] information",
            current_user.username,
            current_user.permission.value,
            company.name,
        )
        abort(403, "You don't have access to this company information.")

    logger.info("Sending sftp data of company {}", company.name)
    return (
        jsonify(
            company_sftp_username=company.default_sftp_username,
            company_sftp_password=company.default_sftp_password,
        ),
        200,
    )


@company_blueprint.route("/<int:company_id>/locations", methods=["GET"])
@login_required
def company_locations_list(company_id: int):
    """Returns company locations (id and name) as JSON

    Args:
        company_id (int): company id

    Returns:
        JSON: company locations
    """
    company: m.Company = m.Company.query.get_or_404(company_id)

    # Check if user has access to company information
    if not has_access_to_company(current_user, company):
        abort(403, "You don't have access to this company locations information.")

    # If user has global access or associated with company, return all locations
    match current_user.permission:
        case m.UserPermissionLevel.GLOBAL | m.UserPermissionLevel.COMPANY:
            locations = (
                m.Location.query.filter_by(company_id=company.id)
                .order_by(m.Location.name)
                .all()
            )
        case m.UserPermissionLevel.LOCATION_GROUP:
            locations = current_user.location_group[0].locations
        case m.UserPermissionLevel.LOCATION:
            locations = current_user.location
        case _:
            locations = []

    res = [(location.id, location.name) for location in locations]

    return jsonify(locations=res), 200


@company_blueprint.route("/<int:company_id>/locations-for-groups", methods=["GET"])
@login_required
def company_locations_for_groups(company_id: int):
    """
    Returns company locations (id and name) as JSON
    Returns only locations that are not associated with any group

    Args:
        company_id (int): company id

    Returns:
        JSON: company locations
    """
    # Check if user has access to information
    if (
        current_user.permission != m.UserPermissionLevel.GLOBAL
        or current_user.role != m.UserRole.ADMIN
    ):
        abort(403, "You don't have access to this information.")

    # Find all company locations that are not associated with any group
    locations = m.Location.query.filter_by(company_id=company_id).all()

    group_id = request.args.get("group_id")

    if group_id:
        res = [
            (location.id, location.name)
            for location in locations
            if not location.group or location.group[0].id == int(group_id)
        ]
    else:
        res = [
            (location.id, location.name) for location in locations if not location.group
        ]

    return jsonify(locations=res), 200


@company_blueprint.route("/<int:company_id>/location-groups", methods=["GET"])
@login_required
def company_location_groups(company_id: int):
    """
    Returns company location groups (id and name) as JSON

    Args:
        company_id (int): company id

    Returns:
        JSON: company location groups
    """
    # Check if user has access to information
    if (
        current_user.permission.value
        not in [m.UserPermissionLevel.GLOBAL.value, m.UserPermissionLevel.COMPANY.value]
        or current_user.role != m.UserRole.ADMIN
    ):
        abort(403, "You don't have access to this information.")

    # Find all company location groups
    location_groups = m.LocationGroup.query.filter_by(company_id=company_id).all()
    res = [(group.id, group.name) for group in location_groups]

    return jsonify(location_groups=res), 200
