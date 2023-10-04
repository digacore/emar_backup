from flask import jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app import models as m

from app.logger import logger


location_blueprint = Blueprint("location_blueprint", __name__, url_prefix="/location")


@location_blueprint.route("/<int:location_id>/sftp_data", methods=["GET"])
@login_required
def location_sftp_data(location_id: int):
    """Returns location sftp data as JSON

    Args:
        location_id (int): location id

    Returns:
        JSON: location sftp data
    """
    location: m.Location = m.Location.query.get_or_404(location_id)

    # Check if user has access to location information
    if (
        current_user.asociated_with.lower() not in ["global-full", "global-view"]
        and current_user.asociated_with != location.name
        and current_user.asociated_with != location.company.name
    ):
        abort(403, "You don't have access to this location information.")

    logger.info("Sending sftp data of location {}", location.name)
    return (
        jsonify(
            default_sftp_path=location.default_sftp_path,
        ),
        200,
    )


@location_blueprint.route("/", methods=["GET"])
@login_required
def all_locations_list():
    """Returns all locations (id and name) as JSON

    Returns:
        JSON: all locations list
    """
    # If user has global access return all locations
    if current_user.asociated_with.lower() in ["global-full", "global-view"]:
        locations = m.Location.query.order_by(m.Location.name).all()
    elif current_user.asociated_with in [
        company.name for company in m.Company.query.all()
    ]:
        locations = (
            m.Location.query.filter_by(company_name=current_user.asociated_with)
            .order_by(m.Location.name)
            .all()
        )
    elif current_user.asociated_with in [
        location.name for location in m.Location.query.all()
    ]:
        locations = (
            m.Location.query.filter_by(name=current_user.asociated_with)
            .order_by(m.Location.name)
            .all()
        )
    else:
        locations = []

    res = [(location.id, location.name) for location in locations]

    return jsonify(locations=res), 200
