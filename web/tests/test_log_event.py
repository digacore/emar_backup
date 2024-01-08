from app.models import Computer, LogType, LogEvent
from app.controllers import create_log_event


def test_create_log_event(test_db):
    test_computer = (
        test_db.session.query(Computer).filter_by(computer_name="comp3_test").first()
    )

    # Create the first log for BACKUP_DOWNLOAD
    create_log_event(test_computer, LogType.BACKUP_DOWNLOAD)
    assert len(test_computer.log_events) == 1
    assert test_computer.log_events[0].log_type == LogType.BACKUP_DOWNLOAD

    # Create the second log for CLIENT_UPGRADE event
    data = "Version: 1.0.16.879870"
    create_log_event(test_computer, LogType.CLIENT_UPGRADE, data=data)
    assert len(test_computer.log_events) == 2

    upgrade_logs = (
        test_db.session.query(LogEvent)
        .filter_by(
            computer_id=test_computer.id,
            log_type=LogType.CLIENT_UPGRADE,
        )
        .all()
    )
    assert len(upgrade_logs) == 1
    assert upgrade_logs[0].data == data
