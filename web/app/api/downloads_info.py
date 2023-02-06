import datetime
import uuid
import json
from flask import jsonify

from app.models import Computer
from app.schema import GetCredentials, LastTime, DownloadStatus, FilesChecksum
from app.views.blueprint import BlueprintApi
from app.logger import logger
from config import EST


downloads_info_blueprint = BlueprintApi("/downloads_info", __name__)


@downloads_info_blueprint.post("/last_time")
@logger.catch
def last_time(body: LastTime):
    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
        body.identifier_key else None

    if computer:
        logger.info(f"Updating last download time for computer: {computer.computer_name}.")
        # TODO convert to Datetime object. Looks like str(datetime) from local computer is ok
        computer.last_download_time = body.last_download_time
        computer.last_time_online = body.last_time_online
        computer.update()
        logger.info(f"Last download time for computer {computer.computer_name} is updated.")
        return jsonify(status="success", message="Writing time to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Last download time update failed. computer_name: {computer.computer_name}, \
        location {computer.location_name}. Reason: {message}")
    return jsonify(status="fail", message=message), 400


@downloads_info_blueprint.post("/get_credentials")
@logger.catch
def get_credentials(body: GetCredentials):

    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key,
        computer_name=body.computer_name
        ).first() if body.identifier_key else None

    computer_name: Computer = Computer.query.filter_by(
            computer_name=body.computer_name
        ).first()

    if computer:
        print("computer: ", computer, computer.computer_name)
        computer.last_time_online = datetime.datetime.now(EST())
        computer.identifier_key = str(uuid.uuid4())
        computer.update()
        logger.info(f"Updated identifier_key for computer {computer.computer_name}.")
        logger.info(f"Supplying credentials for computer {computer.computer_name}.")

        remote_files_checksum = computer.files_checksum if computer.files_checksum else {}

        print("computer data:",
            computer.sftp_host,
            computer.company_name,
            computer.location_name,
            computer.sftp_username,
            computer.sftp_password,
            computer.sftp_folder_path,
            computer.identifier_key,
            computer.manager_host,
            computer.files_checksum
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
            manager_host=computer.manager_host,
            files_checksum=json.loads(str(remote_files_checksum))
            ), 200
    
    elif computer_name:
        message = "Wrong id."
        logger.info(f"Supplying credentials failed. computer: {body.computer_name}, \
            id {body.identifier_key}. Reason: {message}")
        return jsonify(status="fail", message=message), 400

    message = "Wrong request data. Computer not found."
    logger.info(f"Supplying credentials failed. computer: {body.computer_name}, \
        id {body.identifier_key}. Reason: {message}. Removing local credentials.")
    return jsonify(status="fail", message=message, rmcreds="rmcreds"), 400


@downloads_info_blueprint.post("/download_status")
@logger.catch
def download_status(body: DownloadStatus):

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
        body.identifier_key else None

    if computer:
        logger.info(f"Updating download status for computer: {computer.computer_name}.")
        computer.last_time_online = datetime.datetime.now(EST())
        computer.download_status = body.download_status
        if body.last_downloaded:
            computer.last_downloaded = body.last_downloaded
        computer.update()
        logger.info(f"Download status for computer {computer.computer_name} is updated to {body.download_status}.")

        return jsonify(status="success", message="Writing download status to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Download status update failed. computer_name: {computer.computer_name}, \
        location {computer.location_name}. Reason: {message}")
    return jsonify(status="fail", message=message), 400


@downloads_info_blueprint.post("/files_checksum")
@logger.catch
def files_checksum(body: FilesChecksum):

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first() if \
        body.identifier_key else None

    if computer:
        logger.info(f"Updating files checksum for computer: {computer.computer_name}.")
        computer.last_time_online = datetime.datetime.now(EST())
        computer.files_checksum = json.dumps(body.files_checksum)
        computer.update()
        logger.info(f"Files checksum for computer {computer.computer_name} is updated to {body.files_checksum}.")

        return jsonify(status="success", message="Writing files checksum to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Files checksum update failed. computer_name: {computer.computer_name}, \
        location {computer.location_name}. Reason: {message}")
    return jsonify(status="fail", message=message), 400
