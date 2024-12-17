import io
import os
from flask import send_file, jsonify, Response, Blueprint

from app.views.blueprint import BlueprintApi
from app.models import DesktopClient, Computer, LogType, Location
from app.schema import LoadMSI, UpdateMSIVersion
from app.controllers import create_log_event

from app.logger import logger


download_msi_blueprint = BlueprintApi("/download_msi", __name__)
download_msi_fblueprint = Blueprint("download_msi", __name__)
# TODO split blueprints


@download_msi_fblueprint.route("/download/<int:id>", methods=["GET"])
@logger.catch
def download_msi(id):
    # TODO add guid, register to db, add to /download/23dc4cccccqd4443c
    msi = DesktopClient.query.filter_by(id=id).first()

    if msi:
        return send_file(
            io.BytesIO(msi.blob), download_name=msi.filename, mimetype=msi.mimetype
        )
    else:
        return jsonify(status="fail", message="Wrong request data."), 400


@download_msi_blueprint.post("/msi_download_to_local")
@logger.catch
def msi_download_to_local(body: LoadMSI):
    computer: Computer = (
        Computer.query.filter_by(identifier_key=body.identifier_key).first()
        if body.identifier_key
        else None
    )

    if computer:
        msi: DesktopClient = (
            DesktopClient.query.filter_by(flag_name=body.flag).first()
            if body.flag == "stable" or body.flag == "latest"
            else DesktopClient.query.filter_by(version=body.version).first()
        )

        if msi:
            logger.info(
                "Giving file {} to computer {}.", msi.name, computer.computer_name
            )
            return Response(
                msi.blob,
                mimetype=msi.mimetype,
                headers={"Content-disposition": f"attachment; filename={msi.filename}"},
            )
        else:
            message = "Wrong request data. Wrong or empty version."
            logger.info(
                "MSI download failed. computer_name: {}. Reason: {}",
                computer.computer_name,
                message,
            )
            return jsonify(status="fail", message=message), 400

    message = "Wrong request data. Computer not found."
    logger.info("MSI download failed. Reason: {}", message)
    return jsonify(status="fail", message=message), 400


@download_msi_blueprint.post("/update_current_msi_version")
@logger.catch
def update_current_msi_version(body: UpdateMSIVersion):
    computer: Computer = (
        Computer.query.filter_by(identifier_key=body.identifier_key).first()
        if body.identifier_key
        else None
    )

    if computer:
        msi: DesktopClient = (
            DesktopClient.query.filter_by(flag_name=body.current_msi_version).first()
            if body.current_msi_version == "stable"
            or body.current_msi_version == "latest"
            else DesktopClient.query.filter_by(version=body.current_msi_version).first()
        )

        current_msi_version = msi.version if msi else "undefined"

        computer.current_msi_version = current_msi_version
        computer.update()

        if computer.logs_enabled:
            create_log_event(
                computer,
                LogType.CLIENT_UPGRADE,
                data=f"New version: {current_msi_version}",
            )

        return (
            jsonify(
                status="success", message=f"Writing version {current_msi_version} to DB"
            ),
            200,
        )

    message = "Wrong request data. Computer not found."
    logger.info("MSI version update failed. Reason: {}", message)
    return jsonify(status="fail", text=message), 400


# Route for downloading MSI with LID (location id)
@download_msi_fblueprint.route("/download_lid/<int:lid>", methods=["GET"])
@logger.catch
def download_lid_msi(lid: int):
    msi = DesktopClient.query.filter_by(flag_name="stable").first()
    if not msi:
        msi = DesktopClient.query.filter_by(flag_name="latest").first()
        if not msi:
            msi = DesktopClient.query.first()
            if not msi:
                return jsonify(status="fail", message="No MSI found."), 400
    location = Location.query.filter_by(id=lid).first()
    base_filename, extension = os.path.splitext(msi.filename)
    filename = f"{base_filename}_lid_{location.id}{extension}"
    if msi and location:
        return send_file(
            io.BytesIO(msi.blob), download_name=filename, mimetype=msi.mimetype
        )
    else:
        return jsonify(status="fail", message="Wrong request data."), 400


@download_msi_fblueprint.route("/download_unprompt_msi", methods=["GET"])
@logger.catch
def download_unprompt_msi():
    msi = DesktopClient.query.filter_by(flag_name="unprompt").first()
    if not msi:
        return jsonify(status="fail", message="No unprompt MSI found."), 400
    return send_file(
        io.BytesIO(msi.blob), download_name=msi.filename, mimetype=msi.mimetype
    )
