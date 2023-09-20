from flask import jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app import models as m

from app.logger import logger


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
    if (
        current_user.asociated_with.lower() not in ["global-full", "global-view"]
        and current_user.asociated_with != company.name
    ):
        logger.error(
            "User [{}] with access level [{}] tried to access company [{}] information",
            current_user.username,
            current_user.asociated_with,
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
    if (
        current_user.asociated_with.lower() not in ["global-full", "global-view"]
        and current_user.asociated_with != company.name
        and current_user.asociated_with
        not in [
            location.name
            for location in m.Location.query.filter_by(company_name=company.name).all()
        ]
    ):
        abort(403, "You don't have access to this company locations information.")

    # If user has global access or associated with company, return all locations
    if (
        current_user.asociated_with.lower() in ["global-full", "global-view"]
        or current_user.asociated_with == company.name
    ):
        locations = (
            m.Location.query.filter_by(company_name=company.name)
            .order_by(m.Location.name)
            .all()
        )
    else:
        locations = [
            m.Location.query.filter_by(name=current_user.asociated_with).first()
        ]

    res = [(location.id, location.name) for location in locations]

    return jsonify(locations=res), 200
