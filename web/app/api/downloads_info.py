import datetime
import uuid
from flask import jsonify

from app.models import Computer
from app.schema import GetCredentials, LastTime, DownloadStatus
from app.views.blueprint import BlueprintApi
from app.logger import logger


downloads_info_blueprint = BlueprintApi("/downloads_info", __name__)
# downloads_info_blueprint = Blueprint("downloads_info", __name__)


@downloads_info_blueprint.post("/last_time")
@logger.catch
def last_time(body: LastTime):
    # TODO set local user password here or on another route?

    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
        body.identifier_key else None

    if computer:
        logger.info(f"Updating last download time for computer: {computer.company_name}.")
        # TODO convert to Datetime object. Looks like str(datetime) from local computer is ok
        computer.last_download_time = body.last_download_time
        computer.last_time_online = body.last_time_online
        computer.update()
        logger.info(f"Last download time for computer {computer.company_name} is updated.")
        return jsonify(status="success", message="Writing time to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Last download time update failed. company_name: {computer.company_name}, \
        location {computer.location_name}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


@downloads_info_blueprint.post("/get_credentials")
@logger.catch
def get_credentials(body: GetCredentials):

    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key,
        computer_name=body.computer_name
        ).first() if body.identifier_key else None

    if computer:
        print("computer: ", computer)
        logger.info(f"Supplying credentials for computer {computer.sftp_username}.")
        computer.last_time_online = datetime.datetime.now()
        computer.identifier_key = str(uuid.uuid4())
        computer.update()
        logger.info(f"Updated identifier_key for computer {computer.sftp_username}.")

        print("computer data:",
            computer.sftp_host,
            computer.company_name,
            computer.location_name,
            computer.sftp_username,
            computer.sftp_password,
            computer.sftp_folder_path,
            computer.identifier_key,
            computer.manager_host
        )

        return jsonify(
            status="success",
            message="Supplying credentials",
            host=computer.sftp_host,
            company_name=computer.company_name,
            location_name=computer.location_name,
            sftp_username=computer.sftp_username,
            sftp_password=computer.sftp_password,
            sftp_folder_path=computer.sftp_folder_path,
            identifier_key=computer.identifier_key,
            computer_name=computer.computer_name,
            folder_password=computer.folder_password,
            manager_host=computer.manager_host
            ), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Supplying credentials failed. computer: {computer.computer_name}, \
        id {computer.identifier_key}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


@downloads_info_blueprint.post("/download_status")
@logger.catch
def download_status(body: DownloadStatus):

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
        body.identifier_key else None

    if computer:
        logger.info(f"Updating download status for computer: {computer.sftp_username}.")
        computer.last_time_online = datetime.datetime.now()
        computer.download_status = body.download_status
        computer.update()
        logger.info(f"Download status for computer {computer.sftp_username} is updated to {body.download_status}.")

        return jsonify(status="success", message="Writing download status to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Download status update failed. company_name: {computer.computer_name}, \
        location {computer.location_name}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


# TODO Email alert
# @route or func??
# def email_alert()
