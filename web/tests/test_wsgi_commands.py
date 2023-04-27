import pytest

from app.controllers import (
    create_superuser,
    check_and_alert,
    empty_to_stable,
    daily_summary,
)
from app.models import User, Computer, Alert

from config import BaseConfig as CFG


def test_create_superuser(client):
    create_superuser()
    superuser: User = User.query.filter_by(username=CFG.SUPER_USER_NAME).first()
    assert superuser
    assert superuser.asociated_with == "global-full"


# @pytest.mark.skip
def test_check_and_alert(client, requests_mock):

    database_computers = {
        "comp1_intime": "green",
        "comp2_late": "yellow - offline over 13 h",
        "comp3_test": "green",
        "comp4_test": "green",
        "comp5_test": "green",
        "comp6_late": "red - no backup over 50 h",
        "comp7_no_download_time": "red - no backup over 999 h",
    }

    computers_before_check = Computer.query.all()

    alerted_computers_before = [
        comp.computer_name
        for comp in computers_before_check
        if "red" in str(comp.alert_status) or "yellow" in str(comp.alert_status)
    ]

    atlas_user: User = User.query.filter_by(username="test_user_company").first()
    no_download_12h: Alert = Alert.query.filter_by(name="no_download_4h").first()
    offline_12h: Alert = Alert.query.filter_by(name="offline_12h").first()

    atlas_user.alerts.append(no_download_12h)
    atlas_user.alerts.append(offline_12h)

    requests_mock.post(
        CFG.MAIL_ALERTS,
        json={"message": "Email alert sent from API", "status": "success"},
    )

    check_and_alert()

    computers_after_check = Computer.query.all()
    alerted_computers_after = [
        comp.computer_name
        for comp in computers_after_check
        if "red" in comp.alert_status or "yellow" in comp.alert_status
    ]

    assert len(alerted_computers_before) != alerted_computers_after

    computers = {comp.computer_name: comp for comp in Computer.query.all()}
    for comp in computers:
        assert database_computers[comp] == computers[comp].alert_status

    # TODO consider case when there are >2 computers in 1 location
    # first computer becomes yellow
    # second becomes red
    # check again to make first also red
    # check_and_alert()


def test_empty_to_stable(client):
    computer5: Computer = Computer.query.filter_by(computer_name="comp5_test").first()
    computer5.msi_version = None
    computer5.update()

    empty_computers = Computer.query.filter_by(msi_version=None).all()
    empty_to_stable()
    no_empty_computers = Computer.query.filter_by(msi_version=None).all()

    assert len(empty_computers) > 0
    assert len(no_empty_computers) == 0


def test_daily_summary(client, requests_mock):

    requests_mock.post(
        CFG.MAIL_ALERTS,
        json={"message": "Email alert sent from API", "status": "success"},
    )

    daily_summary()
