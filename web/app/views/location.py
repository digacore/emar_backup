from flask import jsonify, Blueprint, abort
from flask_login import login_required, current_user

from app import models as m

from app.logger import logger

from .utils import has_access_to_location


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
    if not has_access_to_location(current_user, location):
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
    match current_user.permission:
        case m.UserPermissionLevel.GLOBAL:
            locations = m.Location.query.order_by(m.Location.name).all()
        case m.UserPermissionLevel.COMPANY:
            locations = (
                m.Location.query.filter_by(company_id=current_user.company_id)
                .order_by(m.Location.name)
                .all()
            )
        case m.UserPermissionLevel.LOCATION_GROUP:
            locations = (
                m.Location.query.filter(
                    m.Location.id.in_(
                        [
                            location.id
                            for location in current_user.location_group[0].locations
                        ]
                    )
                )
                .order_by(m.Location.name)
                .all()
            )
        case m.UserPermissionLevel.LOCATION:
            locations = m.Location.query.filter_by(id=current_user.location[0].id).all()
        case _:
            locations = []

    res = [(location.id, location.name) for location in locations]

    return jsonify(locations=res), 200
