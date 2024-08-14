import random
from datetime import datetime, timedelta

from app.logger import logger
from app.models import Computer, LogEvent, LogType


def create_log_event(
    computer: Computer,
    log_type: LogType,
    data: str | None = None,
    created_at: datetime | None = None,
):
    """Create new log event for computer

    Args:
        computer (m.Computer): Computer object
        log_type (m.LogType): Log type
        data (str, optional): Data for log. Defaults to None.
        created_at (datetime, optional): log creation time. Defaults to None.
    """
    new_log = LogEvent(
        log_type=log_type,
        computer_id=computer.id,
        created_at=created_at if created_at else datetime.utcnow(),
        data=data if data else "",
    )

    new_log.save()

    # logger.debug("New log event created: {}", new_log)


def gen_fake_backup_download_logs(computer: Computer, time_period: timedelta):
    """Generate fake backup logs for computer

    Args:
        computer (m.Computer): Computer object
        time_period (timedelta): Time period for logs
    """
    # Set up list of working hours
    WORKING_HOURS = tuple(range(8, 13)) + tuple(range(14, 23))

    # Check if there are any logs exist for this computer
    current_logs = LogEvent.query.filter_by(computer_id=computer.id).all()
    if current_logs:
        logger.info("Logs already exist for computer {}", computer)
        return

    log_time = datetime.utcnow() - time_period
    total_logs = 0

    for hour in range(time_period.days * 24 + time_period.seconds // 3600):
        random_number = random.randint(1, 10)
        if log_time.hour in WORKING_HOURS and random_number != 10:
            create_log_event(computer, LogType.BACKUP_DOWNLOAD, created_at=log_time)
            total_logs += 1

        log_time += timedelta(hours=1)

    logger.info(
        "<-----{} fake backup logs was generated for computer {}----->",
        total_logs,
        computer,
    )
