import datetime
import uuid
from flask import jsonify

from app.models import Computer
from app.schema import ComputerRegInfo
from app.views.blueprint import BlueprintApi
from app.logger import logger


computer_blueprint = BlueprintApi("/computer", __name__)


@computer_blueprint.post("/register_computer")
@logger.catch
def register_computer(body: ComputerRegInfo):
    # TODO set local user password here or on another route?

    # TODO use some token to secure api routes

    computer: Computer = Computer.query.filter_by(
            identifier_key=body.identifier_key,
            computer_name=body.computer_name
        ).first()
    
    computer_name: Computer = Computer.query.filter_by(
            computer_name=body.computer_name
        ).first()

    if computer:
        message = "Wrong request data. Such computer already exists"
        logger.info(f"Computer registration failed. Reason: {message}")
        return jsonify(status="fail", message=message), 404

    elif computer_name:
        message = "Such computer_name already exists. Wrong computer id."
        logger.info(f"Computer registration failed. Reason: {message}")
        return jsonify(status="fail", message=message), 404

    elif body.identifier_key == "new_computer":
        new_identifier_key = str(uuid.uuid4())
        logger.info(f"Registering computer. ID = {new_identifier_key}.")
        
        new_computer = Computer(
            identifier_key=new_identifier_key,
            computer_name=body.computer_name,
        )
        new_computer.save()
        logger.info(f"Computer registered. ID = {new_identifier_key}.")
        return jsonify(
            status="registered",
            message="Supplying credentials",
            host="",
            company_name="",
            location="",
            sftp_username="",
            sftp_password="",
            sftp_folder_path="",
            identifier_key=new_computer.identifier_key,
            computer_name=new_computer.computer_name,
            folder_password=""
            ), 200

    else:
        message = "Wrong request data."
        logger.info(f"Computer registration failed. Reason: {message}")
        return jsonify(status="fail", message=message), 404
