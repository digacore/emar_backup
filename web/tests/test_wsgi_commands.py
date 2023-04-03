from app.controllers import create_superuser, check_and_alert, empty_to_stable
from app.models import User, Computer

from config import BaseConfig as CFG


def test_create_superuser(client):
    create_superuser()
    superuser: User = User.query.filter_by(username=CFG.SUPER_USER_NAME).first()
    assert superuser
    assert superuser.asociated_with == "global-full"


def test_check_and_alert(client):
    # check_and_alert()  # TODO test this func
    pass


def test_empty_to_stable(client):
    empty_computers = Computer.query.filter_by(msi_version=None).all()
    empty_to_stable()
    no_empty_computers = Computer.query.filter_by(msi_version=None).all()

    assert len(empty_computers) > 0
    assert len(no_empty_computers) == 0
