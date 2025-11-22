from flask import url_for

from app import models as m
from app.controllers import create_system_log


def test_create_log_event(client, test_db):
    test_computer = (
        test_db.session.query(m.Computer).filter_by(computer_name="comp3_test").first()
    )

    test_user = (
        test_db.session.query(m.User).filter_by(username="test_user_company").first()
    )
    test_company = test_db.session.query(m.Company).filter_by(name="Atlas").first()

    # Create the first log for COMPUTER_CREATED log type
    create_system_log(m.SystemLogType.COMPUTER_CREATED, test_computer, test_user)
    assert len(m.SystemLog.query.all()) == 1

    first_created_log = m.SystemLog.query.first()
    assert first_created_log.log_type == m.SystemLogType.COMPUTER_CREATED
    assert first_created_log.object_id == test_computer.id
    assert first_created_log.object_name == test_computer.computer_name
    assert first_created_log.object_url == url_for(
        "computer.edit_view", id=test_computer.id
    )
    assert first_created_log.created_by_id == test_user.id

    # Create the second log for COMPANY_UPDATED log type
    create_system_log(m.SystemLogType.COMPANY_UPDATED, test_company, test_user)

    assert len(m.SystemLog.query.all()) == 2

    second_created_log = m.SystemLog.query.filter_by(
        log_type=m.SystemLogType.COMPANY_UPDATED
    ).first()
    assert second_created_log.log_type == m.SystemLogType.COMPANY_UPDATED
    assert second_created_log.object_id == test_company.id
    assert second_created_log.object_name == test_company.name
    assert second_created_log.object_url == url_for(
        "company.edit_view", id=test_company.id
    )
    assert second_created_log.created_by_id == test_user.id
