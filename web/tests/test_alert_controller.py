from app.controllers.alert import alert_additional_users
from app.models import Computer, Alert, User
from app import db

from config import BaseConfig as CFG


def test_alert_additional_users(client, requests_mock):

    user: User = User.query.filter_by(username="test_user_company").first()
    computer: Computer = Computer.query.filter_by(computer_name="comp4_test").first()
    alert_obj: Alert = Alert.query.filter_by(name="no_download_12h").first()

    user.alerts.append(alert_obj)
    db.session.commit()

    requests_mock.post(
        CFG.MAIL_ALERTS,
        json={"message": "Email alert sent from API", "status": "success"},
    )

    alert_additional_users(computer, alert_obj)

    # assert WHAT?
