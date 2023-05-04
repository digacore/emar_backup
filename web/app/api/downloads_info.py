import datetime
import uuid
import json
from flask import jsonify

from app.models import Computer, DesktopClient
from app.schema import GetCredentials, LastTime, DownloadStatus, FilesChecksum
from app.views.blueprint import BlueprintApi
from app.logger import logger
from config import BaseConfig as CFG


downloads_info_blueprint = BlueprintApi("/downloads_info", __name__)


def check_msi_version(computer: Computer, body, time_type: str):
    """Check for old or new msi version. If old - return datetime.utcnow() + 5
    Else - return datetime.utcnow() + 4

    Args:
        computer (Computer): sqla Computer obj
        time_type (str): "online" or "download"

    Raises:
        ValueError: if time_type != "online" or "download"

    Returns:
        (datetime or str): computer.last_time_online or computer.last_download_time
    """
    lst_times = {
        "online": body.last_time_online,
        "download": body.last_download_time,
    }

    if time_type not in lst_times:
        raise ValueError("Wrong time_type in check_msi_version: {}", time_type)

    current_comp_msi_version = (
        computer.msi_version if computer.msi_version else "stable"
    )

    msi_version: DesktopClient = (
        DesktopClient.query.filter(DesktopClient.flag_name == current_comp_msi_version)
        .with_entities(DesktopClient.version)
        .first()
        if current_comp_msi_version == "stable" or current_comp_msi_version == "latest"
        else DesktopClient.query.filter(
            DesktopClient.version == current_comp_msi_version
        )
        .with_entities(DesktopClient.version)
        .first()
    )

    msi_version: DesktopClient = (
        msi_version
        if msi_version
        else DesktopClient.query.filter(DesktopClient.flag_name == "stable")
        .with_entities(DesktopClient.version)
        .first()
    )

    if int(msi_version.version.replace(".", "")) < int("1.0.9.100769".replace(".", "")):
        return lst_times[time_type] + datetime.timedelta(hours=1)
    return lst_times[time_type]


@downloads_info_blueprint.post("/last_time")
@logger.catch
def last_time(body: LastTime):
    # TODO use some token to secure api routes

    computer: Computer = (
        Computer.query.filter_by(identifier_key=body.identifier_key).first()
        if body.identifier_key
        else None
    )

    computer_name: Computer = Computer.query.filter_by(
        computer_name=body.computer_name
    ).first()

    if computer:
        logger.info(
            "Updating last download/online time for computer: {}. Current time download: {}. Current time online: {}. EST time: {}",
            computer.computer_name,
            computer.last_download_time,
            computer.last_time_online,
            CFG.offset_to_est(datetime.datetime.utcnow(), True),
        )
        # TODO deside which way is better and remove needless one
        # computer.last_time_online = body.last_time_online
        computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow(), True)
        field = "online"
        if body.last_download_time:
            # computer.last_download_time = body.last_download_time
            computer.last_download_time = CFG.offset_to_est(
                datetime.datetime.utcnow(), True
            )
            field = "download/online"
        computer.update()
        logger.info(
            "Last {} time for computer {} is updated. New time download: {}. New time online: {}.",
            field,
            computer.computer_name,
            computer.last_download_time,
            computer.last_time_online,

        )

        msi: DesktopClient = (
            DesktopClient.query.filter_by(flag_name=computer.msi_version).first()
            if computer.msi_version == "stable" or computer.msi_version == "latest"
            else DesktopClient.query.filter_by(version=computer.msi_version).first()
        )

        return (
            jsonify(
                status="success",
                message="Writing time to db",
                sftp_host=computer.sftp_host,
                sftp_username=computer.sftp_username,
                sftp_folder_path=computer.sftp_folder_path,
                manager_host=computer.manager_host,
                msi_version=msi.version if msi else "undefined",
            ),
            200,
        )

    elif computer_name:
        message = "Wrong id."
        logger.info(
            "Last download/online time update failed. computer: {}, \
            id {}. Reason: {}",
            body.computer_name,
            body.identifier_key,
            message,
        )
        return jsonify(status="fail", message=message), 400

    message = "Wrong request data. Computer not found."
    logger.info(
        "Last download/online time update failed. computer: {}, id {}. \
        Reason: {}. Removing local credentials.",
        body.computer_name,
        body.identifier_key,
        message,
    )
    return jsonify(status="fail", message=message, rmcreds="rmcreds"), 400


@downloads_info_blueprint.post("/get_credentials")
@logger.catch
def get_credentials(body: GetCredentials):
    # TODO add unique guid to headers in server_connect.py for api
    computer: Computer = (
        Computer.query.filter_by(
            identifier_key=body.identifier_key, computer_name=body.computer_name
        ).first()
        if body.identifier_key
        else None
    )

    computer_name: Computer = Computer.query.filter_by(
        computer_name=body.computer_name
    ).first()

    if computer:
        # TODO couses error in tests but works ok on server
        # computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow())
        computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow(), True)
        computer.identifier_key = str(uuid.uuid4())
        computer.update()
        # logger.info("Updated identifier_key for computer {}.", computer.computer_name)
        logger.info("Supplying credentials for computer {}.", computer.computer_name)

        remote_files_checksum = (
            computer.files_checksum if computer.files_checksum else {}
        )

        msi: DesktopClient = (
            DesktopClient.query.filter_by(flag_name=computer.msi_version).first()
            if computer.msi_version == "stable" or computer.msi_version == "latest"
            else DesktopClient.query.filter_by(version=computer.msi_version).first()
        )

        return (
            jsonify(
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
                files_checksum=json.loads(str(remote_files_checksum)),
                msi_version=msi.version if msi else "undefined",
            ),
            200,
        )

    elif computer_name:
        message = "Wrong id."
        logger.info(
            "Supplying credentials failed. computer: {}, \
            id {}. Reason: {}",
            body.computer_name,
            body.identifier_key,
            message,
        )
        return jsonify(status="fail", message=message), 400

    message = "Wrong request data. Computer not found."
    logger.info(
        "Supplying credentials failed. computer: {}, id {}. \
        Reason: {}. Removing local credentials.",
        body.computer_name,
        body.identifier_key,
        message,
    )
    return jsonify(status="fail", message=message, rmcreds="rmcreds"), 400


@downloads_info_blueprint.post("/download_status")
@logger.catch
def download_status(body: DownloadStatus):

    computer: Computer = (
        Computer.query.filter_by(identifier_key=body.identifier_key).first()
        if body.identifier_key
        else None
    )

    if computer:
        logger.info(
            "Updating download status for computer: {} to {}.",
            computer.computer_name,
            CFG.offset_to_est(datetime.datetime.utcnow(), True),
        )
        # TODO couses error in tests but works ok on server
        # computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow())
        computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow(), True)
        computer.download_status = body.download_status
        if body.last_downloaded:
            computer.last_downloaded = body.last_downloaded
        computer.update()
        logger.info(
            "Download status for computer {} is updated to {}.",
            computer.computer_name,
            body.download_status,
        )

        return jsonify(status="success", message="Writing download status to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(
        "Download status update failed. company_name: {}, \
        location {}. Reason: {}",
        body.company_name,
        body.location_name,
        message,
    )
    return jsonify(status="fail", message=message), 400


@downloads_info_blueprint.post("/files_checksum")
@logger.catch
def files_checksum(body: FilesChecksum):

    computer: Computer = (
        Computer.query.filter_by(identifier_key=body.identifier_key).first()
        if body.identifier_key
        else None
    )

    if computer:
        logger.info("Updating files checksum for computer: {}.", computer.computer_name)
        # TODO couses error in tests but works ok on server
        # computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow())
        computer.last_time_online = CFG.offset_to_est(datetime.datetime.utcnow(), True)
        computer.files_checksum = json.dumps(body.files_checksum)
        computer.update()
        logger.info(
            "Files checksum for computer {} is updated to {}.",
            computer.computer_name,
            body.files_checksum,
        )

        return jsonify(status="success", message="Writing files checksum to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Files checksum update failed. Reason: {message}")
    return jsonify(status="fail", message=message), 400
