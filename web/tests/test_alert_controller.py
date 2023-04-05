from app.controllers.alert import alert_additional_users
from app.models import Computer, Alert, User
from app import db


def test_alert_additional_users(client):
    user: User = User.query.filter_by(username="test_user_company").first()
    computer: Computer = Computer.query.filter_by(computer_name="comp4_test").first()
    alert_obj: Alert = Alert.query.filter_by(name="no_download_12h").first()

    user.alerts.append(alert_obj)
    db.session.commit()

    response = alert_additional_users(computer, alert_obj)

    assert response.status_code == 200
