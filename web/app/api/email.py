from flask import jsonify

from app import mail
from app.schema import EmailSchema
from flask_mail import Message
from app.views.blueprint import BlueprintApi
from app.models import Computer

from app.logger import logger


api_email_blueprint = BlueprintApi("/api_email", __name__)


@api_email_blueprint.post("/api_email_alert")
@logger.catch
def api_email_alert(body: EmailSchema):
    # TODO add some token to secure route
    alerted_computer = None
    alerted_computers = None

    if body.alerted_target == "all":
        alerted_computers: Computer = Computer.query.all()
    elif isinstance(body.alerted_target, str):
        alerted_computer: Computer = Computer.query.filter_by(computer_name=body.alerted_target).first()
    else:
        logger.warning("Something went wrong on api_email_alert route during query")

    if alerted_computer:
        alerted_computer.alert_status = body.alert_status
        alerted_computer.update()
    elif alerted_computers:
        for comp in alerted_computers:
            comp.alert_status = body.alert_status
            comp.update()
    else:
        logger.warning("Something went wrong on api_email_alert route during DB update")

    # if some_key:
    if body:
        html_body = body.html_body if body.html_body else ""

        msg = Message(
            subject=body.subject,
            body=body.body,
            recipients=[body.to_addresses],
            html=html_body)

        if body.from_email:
            msg.sender = body.from_email

        mail.send(msg)

        logger.info("Email sent from {} to {}. Subject: {}", body.from_email, body.to_addresses, body.subject)
        return jsonify(status="success", message="Email alert sent from API"), 200

    message = "Wrong request data."
    logger.info(
        "Failed to send email from {} to {}. Subject: {}. Reason: {}",
        body.from_email, body.to_addresses, body.subject, message
        )
    return jsonify(status="fail", message=message), 404
