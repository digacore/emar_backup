from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import login_required, current_user

from app import models as m

from app.logger import logger

from .utils import has_access_to_computer, get_telemetry_settings_for_computer


computer_settings_blueprint = Blueprint(
    "computer_settings", __name__, url_prefix="/computer_settings"
)


@computer_settings_blueprint.route("/<int:computer_id>", methods=["GET"])
@login_required
def settings_list(computer_id: int):
    computer: m.Computer = m.Computer.query.filter_by(id=computer_id).first()

    if not computer:
        logger.error("Computer with id [{}] not found", computer_id)
        abort(404, "Computer not found.")
    # Check if user has access to location information
    if not has_access_to_computer(current_user, computer):
        abort(403, "You don't have access to this computer information.")

    telemetry_settings = get_telemetry_settings_for_computer(computer)

    return render_template(
        "computer_settings/computer_settings.html",
        computer=computer,
        telemetry_settings=telemetry_settings,
    )


@computer_settings_blueprint.route(
    "/update_printer_info/<int:computer_id>", methods=["POST"]
)
@login_required
def update_printer_info(computer_id: int):
    computer: m.Computer = m.Computer.query.filter_by(id=computer_id).first()

    if not computer:
        logger.error("Computer with id [{}] not found", computer_id)
        abort(404, "Computer not found.")
    # Check if user has access to location information
    if not has_access_to_computer(current_user, computer):
        abort(403, "You don't have access to this computer information.")

    telemetry_settings = get_telemetry_settings_for_computer(computer)
    status = request.values.get("new_status").lower() == "true"

    if telemetry_settings.send_printer_info != status:
        # check is there link table for this computer
        linked_table = m.ComputerSettingsLinkTable.query.filter_by(
            computer_id=computer.id
        ).first()
        if linked_table:
            # update telemetry settings
            telemetry_settings = m.TelemetrySettings.query.filter_by(
                id=linked_table.telemetry_settings_id
            ).first()
            telemetry_settings.send_printer_info = status
            telemetry_settings.save()
        else:
            # create link table
            telemetry_settings = m.TelemetrySettings(send_printer_info=status)
            telemetry_settings.save()
            new_link_table = m.ComputerSettingsLinkTable(
                computer_id=computer.id, telemetry_settings_id=telemetry_settings.id
            )
            new_link_table.save()

        return render_template(
            "computer_settings/computer_settings.html",
            computer=computer,
            telemetry_settings=telemetry_settings,
        )

    return render_template(
        "computer_settings/computer_settings.html",
        computer=computer,
        telemetry_settings=telemetry_settings,
    )


@computer_settings_blueprint.route("/<int:computer_id>/notes", methods=["GET"])
@login_required
def notes(computer_id: int):
    computer: m.Computer = m.Computer.query.filter_by(id=computer_id).first()

    if not computer:
        logger.error("Computer with id [{}] not found", computer_id)
        abort(404, "Computer not found.")
    # Check if user has access to location information
    if not has_access_to_computer(current_user, computer):
        abort(403, "You don't have access to this computer information.")

    logger.info("Sending notes of computer {}", computer.computer_name)
    return (
        jsonify(
            notes=computer.notes,
        ),
        200,
    )


@computer_settings_blueprint.route("/<int:computer_id>/save_notes", methods=["POST"])
@login_required
def save_notes(computer_id: int):
    computer: m.Computer = m.Computer.query.filter_by(id=computer_id).first()
    notes = request.form.get("notes")
    if not computer:
        logger.error("Computer with id [{}] not found", computer_id)
        abort(404, "Computer not found.")
    # Check if user has access to location information
    if not has_access_to_computer(current_user, computer):
        abort(403, "You don't have access to this computer information.")
    computer.notes = notes
    computer.save()

    logger.info("Saving notes for computer {}", computer.computer_name)
    return ("ok", 200)
