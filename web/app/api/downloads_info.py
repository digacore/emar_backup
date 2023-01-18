import datetime
import uuid
from flask import jsonify

from app.models import User
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

    user: User = User.query.filter_by(identifier_key=body.identifier_key).first() if body.identifier_key else None

    if user:
        logger.info(f"Updating last download time for user: {user.sftp_username}.")
        # TODO convert to Datetime object. Looks like str(datetime) from local user is ok
        user.last_download_time = body.last_download_time
        user.last_time_online = body.last_time_online
        user.update()
        logger.info(f"Last download time for user {user.sftp_username} is updated.")
        return jsonify(status="success", message="Writing time to db"), 200

    message = "Wrong request data. User not found."
    logger.info(f"Last download time update failed. Client: {body.client}, location {body.location}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


@downloads_info_blueprint.post("/get_credentials")
@logger.catch
def get_credentials(body: GetCredentials):

    print("body data:", body.client, body.identifier_key, body.location)

    user: User = User.query.filter_by(
        identifier_key=body.identifier_key,
        client=body.client,
        location=body.location
        ).first() if body.identifier_key else None
    
    print("user: ", user)

    if user:
        logger.info(f"Supplying credentials for user {user.sftp_username}.")
        user.last_time_online = datetime.datetime.now()
        user.identifier_key = uuid.uuid4()
        user.update()
        logger.info(f"Updated identifier_key for user {user.sftp_username}.")

        print("user data:",
            user.sftp_host,
            user.client,
            user.location,
            user.sftp_username,
            user.sftp_password,
            user.sftp_folder_path,
            user.identifier_key
        )

        return jsonify(
            status="success",
            message="Supplying credentials",
            host=user.sftp_host,
            client=user.client,
            location=user.location,
            sftp_username=user.sftp_username,
            sftp_password=user.sftp_password,
            sftp_folder_path=user.sftp_folder_path,
            identifier_key=user.identifier_key
            ), 200

    message = "Wrong request data. User not found."
    logger.info(f"Supplying credentials failed. Client: {body.client}, location {body.location}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


@downloads_info_blueprint.post("/download_status")
@logger.catch
def download_status(body: DownloadStatus):

    user: User = User.query.filter_by(identifier_key=body.identifier_key).first() if body.identifier_key else None

    if user:
        logger.info(f"Updating download status for user: {user.sftp_username}.")
        user.last_time_online = datetime.datetime.now()
        user.download_status = body.download_status
        user.update()
        logger.info(f"Download status for user {user.sftp_username} is updated to {body.download_status}.")

        return jsonify(status="success", message="Writing download status to db"), 200

    message = "Wrong request data. User not found."
    logger.info(f"Download status update failed. Client: {body.client}, location {body.location}. Reason: {message}")
    return jsonify(status="fail", message=message), 404


# TODO Email alert
# @route or func??
# def email_alert()
