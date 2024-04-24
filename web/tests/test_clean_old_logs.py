from datetime import datetime, timedelta, timezone

from app import models as m
from app.controllers import clean_old_logs
from config import BaseConfig as CFG


def test_clean_old_logs(test_db, add_test_logs):
    # Check that all test logs are in the database
    assert test_db.session.query(m.SystemLog).count() == 2
    assert test_db.session.query(m.BackupLog).count() == 2
    assert test_db.session.query(m.LogEvent).count() == 2

    # Clean old logs
    clean_old_logs()
    utc_now = datetime.now(timezone.utc)
    utc_now_naive = utc_now.replace(tzinfo=None)

    # Check that only valid logs are in the database
    assert test_db.session.query(m.SystemLog).count() == 1
    assert test_db.session.query(
        m.SystemLog
    ).first().created_at > utc_now_naive - timedelta(
        days=CFG.SYSTEM_LOGS_DELETION_PERIOD
    )

    assert test_db.session.query(m.BackupLog).count() == 1
    assert test_db.session.query(
        m.BackupLog
    ).first().end_time > utc_now_naive - timedelta(
        days=CFG.COMPUTER_LOGS_DELETION_PERIOD
    )

    assert test_db.session.query(m.LogEvent).count() == 1
    assert test_db.session.query(
        m.LogEvent
    ).first().created_at > utc_now_naive - timedelta(days=CFG.LOG_EVENT_DELETION_PERIOD)
