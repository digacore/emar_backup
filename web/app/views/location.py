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
        and current_user.asociated_with.replace("Location-", "") != location.name
        and current_user.asociated_with.replace("Company-", "") != location.company.name
    ):
        abort(403, "You don't have access to this location information.")

    logger.info("Sending sftp data of location {}", location.name)
    return (
        jsonify(
            default_sftp_path=location.default_sftp_path,
        ),
        200,
    )
