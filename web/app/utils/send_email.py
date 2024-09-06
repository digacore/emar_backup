from flask_mail import Message

from app import mail
from app.logger import logger
from config import BaseConfig as CFG


def send_email(
    subject: str,
    recipients: list[str],
    html: str,
    sender: str = CFG.MAIL_DEFAULT_SENDER,
):
    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        html=html,
    )

    mail.send(msg)
    logger.info("Email with subject {} was successfully sent", subject)
