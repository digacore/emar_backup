from app.controllers import (
    create_superuser,
    empty_to_stable,
)
from app.models import User, Computer, UserRole, UserPermissionLevel

from config import BaseConfig as CFG


def test_create_superuser(client):
    create_superuser()
    superuser: User = User.query.filter_by(username=CFG.SUPER_USER_NAME).first()
    assert superuser
    assert superuser.company.is_global
    assert superuser.role == UserRole.ADMIN
    assert superuser.permission == UserPermissionLevel.GLOBAL


def test_empty_to_stable(client):
    computer5: Computer = Computer.query.filter_by(computer_name="comp5_test").first()
    computer5.msi_version = None
    computer5.update()

    empty_computers = Computer.query.filter_by(msi_version=None).all()
    empty_to_stable()
    no_empty_computers = Computer.query.filter_by(msi_version=None).all()

    assert len(empty_computers) > 0
    assert len(no_empty_computers) == 0
