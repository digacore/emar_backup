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

    computer: Computer = Computer.query.filter_by(identifier_key=body.identifier_key).first()

    if computer:
        print("Such computer already exists. Something went wrong")
    else:
        logger.info(f"Registering computer. ID = {body.identifier_key}.")
        
        new_computer = Computer(
            identifier_key=body.identifier_key,
            computer_name=body.computer_name,
        )
        new_computer.save()
        logger.info(f"Computer registered. ID = {body.identifier_key}.")
        return jsonify(status="success", message="Writing time to db"), 200

    message = "Wrong request data. Computer not found."
    logger.info(f"Last download time update failed. Client: , location . Reason: {message}")
    return jsonify(status="fail", message=message), 404
