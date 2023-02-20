from app.logger import logger
from app import models as m
from config import BaseConfig as CFG


def create_superuser():
    if not m.User.query.filter(m.User.username == CFG.SUPER_USER_NAME).first():
        user = m.User(
            username=CFG.SUPER_USER_NAME,
            email=CFG.SUPER_USER_MAIL,
            password=CFG.SUPER_USER_PASS,
            asociated_with="global-full",
        )
        user.save()
        logger.info("Superuser created")
    else:
        logger.info("Superuser already exists")
