import uuid
from flask import jsonify

from app.models import Computer
from app.schema import ComputerRegInfo, ComputerSpecialStatus
from app.views.blueprint import BlueprintApi
from app.logger import logger

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

    elif computer_name:
        message = f"Such computer_name: {body.computer_name} already exists. Wrong computer id."
        logger.info("Computer registration failed. Reason: {}", message)
        return jsonify(status="fail", message=message), 409

    elif body.identifier_key == "new_computer":
        new_identifier_key = str(uuid.uuid4())

        new_computer = Computer(
            identifier_key=new_identifier_key,
            computer_name=body.computer_name,
            manager_host=CFG.DEFAULT_MANAGER_HOST,
        )
        new_computer.save()
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


@computer_blueprint.get("/special_status")
@logger.catch
def special_status(body: ComputerSpecialStatus):
    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(
        identifier_key=body.identifier_key, computer_name=body.computer_name
    ).first()

    computer.alert_status = (
        body.special_status if body.special_status in CFG.SPECIAL_STATUSES else "green"
    )
    computer.save()

    return jsonify({"status": "success"}), 200
