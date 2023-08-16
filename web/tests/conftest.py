import pytest
from datetime import datetime, timedelta

from app import db, create_app, models as m
from app.controllers import init_db
from config import BaseConfig as CFG

app = create_app(environment="testing")
app.config["TESTING"] = True


@pytest.fixture
def client():

    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()
        db.drop_all()
        db.create_all()
        init_db(True)
        yield client
        db.session.remove()
        db.drop_all()
        app_ctx.pop()


@pytest.fixture
def test_db():

    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()
        db.drop_all()
        db.create_all()
        init_db(True)
        yield db
        db.session.remove()
        db.drop_all()
        app_ctx.pop()


@pytest.fixture
def add_test_logs(test_db):
    test_user = (
        test_db.session.query(m.User).filter_by(username="test_user_view").first()
    )
    test_computer = (
        test_db.session.query(m.Computer).filter_by(computer_name="comp3_test").first()
    )

    # Create test system logs with different dates
    expired_system_log = m.SystemLog(
        log_type=m.SystemLogType.USER_CREATED,
        created_at=datetime.utcnow()
        - timedelta(days=CFG.SYSTEM_LOGS_DELETION_PERIOD + 1),
        object_id=1,
        object_name="test_system_logs_obj_1",
        object_url="/test_url/test_system_logs_obj_1",
        created_by_id=test_user.id,
    )
    test_db.session.add(expired_system_log)

    valid_system_log = m.SystemLog(
        log_type=m.SystemLogType.USER_CREATED,
        created_at=datetime.utcnow(),
        object_id=2,
        object_name="test_system_logs_obj_2",
        object_url="/test_url/test_system_logs_obj_2",
        created_by_id=test_user.id,
    )
    test_db.session.add(valid_system_log)

    # Create test backup logs with different dates
    expired_computer_log = m.BackupLog(
        backup_log_type=m.BackupLogType.WITH_DOWNLOADS_PERIOD,
        start_time=datetime.utcnow()
        - timedelta(days=CFG.COMPUTER_LOGS_DELETION_PERIOD + 3),
        end_time=datetime.utcnow()
        - timedelta(days=CFG.COMPUTER_LOGS_DELETION_PERIOD + 1),
        computer_id=test_computer.id,
    )
    test_db.session.add(expired_computer_log)

    valid_computer_log = m.BackupLog(
        backup_log_type=m.BackupLogType.WITH_DOWNLOADS_PERIOD,
        start_time=datetime.utcnow() - timedelta(days=2),
        end_time=datetime.utcnow(),
        computer_id=test_computer.id,
    )
    test_db.session.add(valid_computer_log)

    # Create test log events with different dates
    expired_log_event = m.LogEvent(
        log_type=m.LogType.BACKUP_DOWNLOAD,
        created_at=datetime.utcnow()
        - timedelta(days=CFG.LOG_EVENT_DELETION_PERIOD + 1),
        computer_id=test_computer.id,
    )
    test_db.session.add(expired_log_event)

    valid_log_event = m.LogEvent(
        log_type=m.LogType.BACKUP_DOWNLOAD,
        created_at=datetime.utcnow(),
        computer_id=test_computer.id,
    )
    test_db.session.add(valid_log_event)

    test_db.session.commit()
