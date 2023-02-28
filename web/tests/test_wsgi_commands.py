from app.controllers import create_superuser, check_and_alert
from app.models import User

from config import BaseConfig as CFG


def test_create_superuser(client):
    create_superuser()
    superuser: User = User.query.filter_by(username=CFG.SUPER_USER_NAME).first()
    assert superuser
    assert superuser.asociated_with == "global-full"


def test_check_and_alert(client):
    # check_and_alert()  # TODO test this func
    pass
