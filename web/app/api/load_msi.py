import io
from flask import send_file, jsonify, Response, Blueprint
from flask_login import login_required

from app.views.blueprint import BlueprintApi
from app.models import DesktopClient, Computer
from app.schema import LoadMSI, UpdateMSIVersion

from app.logger import logger


download_msi_blueprint = BlueprintApi("/download_msi", __name__)
download_msi_fblueprint = Blueprint("download_msi", __name__)
# TODO split blueprints


@download_msi_fblueprint.route("/download/<int:id>", methods=["GET"])
@logger.catch
@login_required
def download_msi(id):
    # TODO protect by login requierd
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

        if body.flag == "stable" or body.flag == "latest":

            msi: DesktopClient = DesktopClient.query.filter_by(
                flag_name=body.flag
            ).first()

            msi = (
                msi
                if msi
                else DesktopClient.query.filter_by(version=body.version).first()
            )
        else:
            msi: DesktopClient = DesktopClient.query.filter_by(
                version=body.version
            ).first()

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

        computer.current_msi_version = body.current_msi_version
        computer.update()
        return jsonify(status="success", message="Writing version to DB"), 200

    message = "Wrong request data. Computer not found."
    logger.info("MSI version update failed. Reason: {}", message)
    return jsonify(status="fail", text=message), 400
