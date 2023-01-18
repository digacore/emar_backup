from flask import jsonify

from app import sendgrid_client
from app.schema import EmailSchema
from app.views.blueprint import BlueprintApi
from app.logger import logger


api_email_blueprint = BlueprintApi("/api_email", __name__)


@api_email_blueprint.post("/api_email_alert")
@logger.catch
def api_email_alert(body: EmailSchema):
    # TODO add some token to secure route

    if some_key:
        html_body = body.html_body if body.html_body else None
        reply_to_address = body.reply_to_address if body.reply_to_address else None

        sendgrid_client.send_email(
            body.from_email,
            body.to_addresses,
            body.subject,
            body.body,
            html_body=html_body,
            reply_to_address=reply_to_address
        )
        logger.info(f"Email sent from {body.from_email} to {body.to_addresses}. Subject: {body.subject}")
        return jsonify(status="success", message="Email alert sent from API"), 200

    message = "Wrong request data."
    logger.info(f"Failed to send email from {body.from_email} to {body.to_addresses}. Subject: {body.subject}. Reason: {message}")
    return jsonify(status="fail", message=message), 404
