import uuid
from datetime import datetime

from flask import jsonify, request

from app.controllers import create_log_event, create_system_log
from app.logger import logger
from app.models import Computer, Location, LogType, SystemLogType, TelemetrySettings
from app.schema import (
    ComputerRegInfo,
    ComputerRegInfoLid,
    ComputerSpecialStatus,
    TelemetryRequestId,
)
from app.views.blueprint import BlueprintApi
from app.views.utils import get_telemetry_settings_for_computer
from config import BaseConfig as CFG

computer_blueprint = BlueprintApi("/computer", __name__)


@computer_blueprint.post("/register_computer")
@logger.catch
def register_computer(body: ComputerRegInfo):
    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key, computer_name=body.computer_name
    ).first()

    computer_name: Computer = Computer.query.filter_by(
        computer_name=body.computer_name
    ).first()

    if computer:
        message = "Wrong request data. Such computer already exists"
        logger.info("Computer registration failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 409

    elif body.identifier_key == "new_computer" and not computer_name:
        # Check if computer with such name already exists but was deleted
        deleted_computer_query: Computer = (
            Computer.query.with_deleted()
            .filter_by(computer_name=body.computer_name)
            .first()
        )
        deleted_computer = deleted_computer_query and deleted_computer_query.is_deleted

        new_identifier_key = str(uuid.uuid4())

        # Restore deleted computer if it exists
        if deleted_computer:
            deleted_computer_query = deleted_computer_query.restore()
            deleted_computer_query.identifier_key = new_identifier_key
            deleted_computer_query.device_type = body.device_type
            deleted_computer_query.device_role = body.device_role
            deleted_computer_query.logs_enabled = body.enable_logs
            deleted_computer_query.activated = False
            deleted_computer_query.update()

            new_computer = deleted_computer_query

        else:
            new_computer = Computer(
                identifier_key=new_identifier_key,
                computer_name=body.computer_name,
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                activated=False,
                device_type=body.device_type,
                device_role=body.device_role,
                deactivated_at=datetime.utcnow(),
                logs_enabled=body.enable_logs,
                last_time_logs_disabled=None if body.enable_logs else datetime.utcnow(),
            )
            new_computer.save()

        # Create system log that computer was created in the system
        create_system_log(SystemLogType.COMPUTER_CREATED, new_computer, None)
        logger.info(
            "Computer registered. {} identifier_key was set.", body.computer_name
        )
        return (
            jsonify(
                status="registered",
                message="Computer registered",
                host="",
                company_name="",
                location="",
                sftp_username="",
                sftp_password="",
                sftp_folder_path="",
                identifier_key=new_computer.identifier_key,
                computer_name=new_computer.computer_name,
                folder_password="",
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                msi_version="stable",
            ),
            200,
        )

    elif computer_name:
        message = f"Such computer_name: {body.computer_name} already exists. Sending creds to agent."
        logger.info("Computer registration failed. Reason: {}", message)
        return (
            jsonify(
                status="success",
                message="Supplying credentials",
                host="",
                company_name="",
                location="",
                sftp_username="",
                sftp_password="",
                sftp_folder_path="",
                identifier_key=computer_name.identifier_key,
                computer_name=computer_name.computer_name,
                folder_password="",
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                msi_version="stable",
            ),
            200,
        )

    else:
        message = "Wrong request data."
        logger.info("Computer registration failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 400


@computer_blueprint.get("/get_computers")
@logger.catch
def get_computers():
    # TODO use some token to secure api routes

    computers: Computer = Computer.query.all()

    response = {
        i.computer_name: {
            "last_download_time": i.last_download_time,
            "last_time_online": i.last_time_online,
        }
        for i in computers
    }

    return jsonify(response), 200


@computer_blueprint.post("/special_status")
@logger.catch
def special_status(body: ComputerSpecialStatus):
    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key, computer_name=body.computer_name
    ).first()

    if not computer:
        message = f"Computer with such identifier_key: {body.identifier_key} and computer_name: {body.computer_name} doesn't exist"
        logger.info("Computer special status failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 404

    if body.special_status and body.special_status in CFG.SPECIAL_STATUSES:
        computer.download_status = body.special_status
        computer.save()

        if computer.logs_enabled:
            create_log_event(computer, LogType.SPECIAL_STATUS, body.special_status)

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "success"}), 200


# TODO: return on 142 change to negative status after the msi updates on all computers


@computer_blueprint.get("/get_telemetry_info")
@logger.catch
def get_telemetry_info(body: TelemetryRequestId):
    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key
    ).first()

    if not computer:
        message = (
            f"Computer with such identifier_key: {body.identifier_key} doesn't exist"
        )
        logger.info("Computer telemetry info failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 404
    telemetry_settings: TelemetrySettings = get_telemetry_settings_for_computer(
        computer
    )
    return (
        jsonify(
            status="success", send_printer_info=telemetry_settings.send_printer_info
        ),
        200,
    )


@computer_blueprint.get("/delete_computer")
@logger.catch
def delete_computer():
    identifier_key = request.args.get("identifier_key")
    computer: Computer = Computer.query.filter_by(identifier_key=identifier_key).first()

    if not computer:
        message = f"Computer with such identifier_key: {identifier_key} doesn't exist"
        logger.info("Computer delete failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 404

    computer.delete()

    # Create system log that computer was deleted from the system
    create_system_log(SystemLogType.COMPUTER_DELETED, computer, None)
    logger.info("Computer deleted. {}", computer.computer_name)
    return jsonify({"status": "success"}), 200


@computer_blueprint.post("/register_computer_lid")
@logger.catch
def register_computer_lid(body: ComputerRegInfoLid):
    logger.info("register_computer_lid. {} in body.", body.activate_device)
    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key, computer_name=body.computer_name
    ).first()
    location: Location = Location.query.filter_by(id=body.lid).first()
    computer_name: Computer = Computer.query.filter_by(
        computer_name=body.computer_name
    ).first()

    if computer:
        message = "Wrong request data. Such computer already exists"
        logger.info("Computer registration failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 409

    elif body.identifier_key == "new_computer" and not computer_name and location:
        # Check if computer with such name already exists but was deleted
        deleted_computer_query: Computer = (
            Computer.query.with_deleted()
            .filter_by(computer_name=body.computer_name)
            .first()
        )
        deleted_computer = deleted_computer_query and deleted_computer_query.is_deleted

        new_identifier_key = str(uuid.uuid4())

        # Restore deleted computer if it exists
        if deleted_computer:
            deleted_computer_query = deleted_computer_query.restore()
            deleted_computer_query.identifier_key = new_identifier_key
            deleted_computer_query.location_id = location.id
            deleted_computer_query.company_id = location.company_id
            deleted_computer_query.device_type = body.device_type
            deleted_computer_query.device_role = body.device_role
            deleted_computer_query.logs_enabled = body.enable_logs
            deleted_computer_query.activated = body.activate_device
            deleted_computer_query.update()

            new_computer = deleted_computer_query

        else:
            new_computer = Computer(
                identifier_key=new_identifier_key,
                computer_name=body.computer_name,
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                device_type=body.device_type,
                device_role=body.device_role,
                logs_enabled=body.enable_logs,
                activated=body.activate_device,
                last_time_logs_enabled=datetime.utcnow() if body.enable_logs else None,
                last_time_logs_disabled=None if body.enable_logs else datetime.utcnow(),
                location_id=location.id,
                company_id=location.company_id,
            )
            new_computer.save()

        # Create system log that computer was created in the system
        create_system_log(SystemLogType.COMPUTER_CREATED, new_computer, None)
        logger.info(
            "Computer registered. {} identifier_key was set.", body.computer_name
        )
        return (
            jsonify(
                status="success",
                message="Supplying credentials",
                host=new_computer.sftp_host,
                company_name=new_computer.company_name,
                location_name=new_computer.location_name,
                sftp_username=new_computer.sftp_username,
                sftp_password=new_computer.sftp_password,
                sftp_folder_path=new_computer.sftp_folder_path,
                identifier_key=new_computer.identifier_key,
                computer_name=new_computer.computer_name,
                folder_password=new_computer.folder_password,
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                msi_version="stable",
            ),
            200,
        )

    elif computer_name:
        message = f"Such computer_name: {body.computer_name} already exists. Wrong computer id."
        logger.info("Computer registration failed. Reason: {}", message)
        return (
            jsonify(
                status="success",
                message="Supplying credentials",
                host="",
                company_name="",
                location="",
                sftp_username="",
                sftp_password="",
                sftp_folder_path="",
                identifier_key=computer_name.identifier_key,
                computer_name=computer_name.computer_name,
                folder_password="",
                manager_host=CFG.DEFAULT_MANAGER_HOST,
                msi_version="stable",
            ),
            200,
        )

    else:
        message = "Wrong request data."
        logger.info("Computer registration failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 400
