import io
from flask import send_file, jsonify, Response
from app.views.blueprint import BlueprintApi
from app.models import DesktopClient, Computer
from app.schema import LoadMSI

from app.logger import logger


download_msi_blueprint = BlueprintApi("/download_msi", __name__)


@download_msi_blueprint.get("/download/<int:id>")
@logger.catch
def download_msi(id):
    _msi = DesktopClient.query.get_or_404(id)
    return send_file(
        io.BytesIO(_msi.blob),
        attachment_filename=_msi.filename,
        mimetype=_msi.mimetype
    )


@download_msi_blueprint.post("/msi_download_to_local")
@logger.catch
def msi_download_to_local(body: LoadMSI):
    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
                         body.identifier_key else None

    if computer:
        if body.flag == "stable" or body.flag == "latest":
            msi: DesktopClient = DesktopClient.query.filter_by(flag_name=body.flag).first()
        else:
            msi: DesktopClient = DesktopClient.query.filter_by(version=body.version).first()

        if msi:
            logger.info("Giving file {} to computer {}.", msi.name, computer.computer_name)
            return Response(
                msi.blob,
                mimetype=msi.mimetype,
                headers={"Content-disposition": f"attachment; filename={msi.filename}"}
            )
        else:
            message = "Wrong request data. Wrong or empty version."
            logger.info("MSI download failed. computer_name: {}. Reason: {}", computer.computer_name, message)
            return jsonify(status="fail", message=message), 400

    message = "Wrong request data. Computer not found."
    logger.info("MSI download failed. Reason: {}", message)
    return jsonify(status="fail", message=message), 400