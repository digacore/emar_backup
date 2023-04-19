import pytest

from app.controllers import create_superuser, check_and_alert, empty_to_stable
from app.models import User, Computer, Alert

from config import BaseConfig as CFG


def test_create_superuser(client):
    create_superuser()
    superuser: User = User.query.filter_by(username=CFG.SUPER_USER_NAME).first()
    assert superuser
    assert superuser.asociated_with == "global-full"


# @pytest.mark.skip
def test_check_and_alert(client, requests_mock):

    alerted_computers_query = Computer.query.filter(
        Computer.alert_status.in_(
            (
                "yellow",
                "yellow - no_download_12h",
                "yellow - offline_12h",
                "red",
                "red - no_download_12h",
                "red - offline_12h",
            )
        )
    )

    alerted_computers_before = alerted_computers_query.all()

    atlas_user: User = User.query.filter_by(username="test_user_company").first()
    no_download_12h: Alert = Alert.query.filter_by(name="no_download_12h").first()
    offline_12h: Alert = Alert.query.filter_by(name="offline_12h").first()

    atlas_user.alerts.append(no_download_12h)
    atlas_user.alerts.append(offline_12h)

    requests_mock.post(
        CFG.MAIL_ALERTS,
        json={"message": "Email alert sent from API", "status": "success"},
    )

    check_and_alert()

    alerted_computers_after = alerted_computers_query.all()

    assert len(alerted_computers_before) != alerted_computers_after


def test_empty_to_stable(client):
    computer5: Computer = Computer.query.filter_by(computer_name="comp5_test").first()
    computer5.msi_version = None
    computer5.update()

    empty_computers = Computer.query.filter_by(msi_version=None).all()
    empty_to_stable()
    no_empty_computers = Computer.query.filter_by(msi_version=None).all()

    assert len(empty_computers) > 0
    assert len(no_empty_computers) == 0
