import enum
import random
from datetime import datetime, timedelta

from app import models as m
from app.logger import logger


class BackupLogError(enum.Enum):
    ONE_HOUR = "Longer than 1 hour without a backup"
    TWO_HOURS = "Longer than 2 hours without a backup"


def create_or_update_backup_period_log(
    computer: m.Computer,
    current_time: datetime = datetime.utcnow(),
):
    """Create or update backup log for computer

    Args:
        computer (m.Computer): Computer object
        backup_log_type (m.BackupLogType): Backup log type
        end_time (datetime): End time of backup log
        error (str | None, optional):  Error for log if it has type WITHOUT_DOWNLOADS_PERIOD. Defaults to None.
        notes (str | None, optional): Note for log if it has type WITHOUT_DOWNLOADS_PERIOD. Defaults to None.
        start_time (datetime | None, optional): Start time of backup log. Defaults to None.
    """
    last_computer_log = (
        m.BackupLog.query.filter_by(computer_id=computer.id)
        .order_by(m.BackupLog.start_time.desc())
        .first()
    )

    # Remove minutes, seconds and microseconds from current time
    rounded_current_time = current_time.replace(minute=0, second=0, microsecond=0)

    # If there is no backup log for this computer - create the first one
    if not last_computer_log:
        new_with_downloads_log = m.BackupLog(
            backup_log_type=m.BackupLogType.WITH_DOWNLOADS_PERIOD,
            start_time=rounded_current_time,
            end_time=rounded_current_time + timedelta(hours=1) - timedelta(seconds=1),
            computer_id=computer.id,
        )
        new_with_downloads_log.save()
        logger.debug("Created first backup log for computer {}", computer.computer_name)
    else:
        # If the last backup log has type WITH_DOWNLOADS_PERIOD
        if last_computer_log.backup_log_type == m.BackupLogType.WITH_DOWNLOADS_PERIOD:
            # If the last backup log end time is less than 1 hour ago - update it
            if last_computer_log.end_time + timedelta(hours=1) > rounded_current_time:
                last_computer_log.end_time = (
                    rounded_current_time + timedelta(hours=1) - timedelta(seconds=1)
                )
                last_computer_log.update()

                logger.debug(
                    "Updated WITH_DOWNLOADS_LOG log for computer {}. Log ID: {}",
                    computer.computer_name,
                    last_computer_log.id,
                )
            # If the last backup log end time is more than 1 hour and 35 minutes ago
            # Create new backup log with type NO_DOWNLOADS_PERIOD and then WITH_DOWNLOADS_PERIOD
            else:
                new_no_downloads_log = m.BackupLog(
                    backup_log_type=m.BackupLogType.NO_DOWNLOADS_PERIOD,
                    start_time=last_computer_log.end_time + timedelta(seconds=1),
                    end_time=rounded_current_time - timedelta(seconds=1),
                    computer_id=computer.id,
                    notes="Device is offline",
                )
                new_no_downloads_log.error = (
                    BackupLogError.TWO_HOURS.value
                    if new_no_downloads_log.duration > timedelta(minutes=59, seconds=59)
                    else BackupLogError.ONE_HOUR.value
                )
                new_no_downloads_log.save()

                new_with_downloads_log = m.BackupLog(
                    backup_log_type=m.BackupLogType.WITH_DOWNLOADS_PERIOD,
                    start_time=new_no_downloads_log.end_time + timedelta(seconds=1),
                    end_time=new_no_downloads_log.end_time + timedelta(hours=1),
                    computer_id=computer.id,
                )
                new_with_downloads_log.save()

                logger.debug(
                    "Created NO_DOWNLOADS_PERIOD and WITH_DOWNLOADS_PERIOD logs for computer {}. Log IDs: {} and {}",
                    computer.computer_name,
                    new_no_downloads_log.id,
                    new_with_downloads_log.id,
                )

        # If the last backup log has type NO_DOWNLOADS_PERIOD
        elif last_computer_log.backup_log_type == m.BackupLogType.NO_DOWNLOADS_PERIOD:
            # Set end time for the last backup log and create new backup log with type WITH_DOWNLOADS_PERIOD
            last_computer_log.end_time = rounded_current_time - timedelta(seconds=1)
            last_computer_log.update()

            new_with_downloads_log = m.BackupLog(
                backup_log_type=m.BackupLogType.WITH_DOWNLOADS_PERIOD,
                start_time=last_computer_log.end_time + timedelta(seconds=1),
                end_time=last_computer_log.end_time + timedelta(hours=1),
                computer_id=computer.id,
            )
            new_with_downloads_log.save()

            logger.debug(
                "Updated NO_DOWNLOADS_PERIOD log and created WITH_DOWNLOADS_PERIOD log for computer {}. \
                    Log IDs: {} and {}",
                computer.computer_name,
                last_computer_log.id,
                new_with_downloads_log.id,
            )


def gen_fake_backup_periods_logs(computer: m.Computer, time_period: timedelta):
    """Generate fake logs about periods with and without backups downloads for computer

    Args:
        computer (m.Computer): Computer object
        time_period (timedelta): Time period for logs
    """
    # Set up list of working hours
    WORKING_HOURS = tuple(range(8, 13)) + tuple(range(14, 23))

    # Check if there are any logs exist for this computer
    current_logs = m.BackupLog.query.filter_by(computer_id=computer.id).all()
    if current_logs:
        logger.info("Backup logs already exist for computer {}", computer)
        return

    log_time = (datetime.utcnow() - time_period).replace(
        minute=0, second=0, microsecond=0
    )

    for hour in range(time_period.days * 24 + time_period.seconds // 3600):
        random_number = random.randint(1, 10)
        random_waiting = timedelta(minutes=random.randint(0, 30))
        if log_time.hour in WORKING_HOURS and random_number != 10:
            create_or_update_backup_period_log(computer, log_time + random_waiting)

        log_time += timedelta(hours=1)

    logger.info(
        "<-----Fake backup periods logs were generated for computer {}----->",
        computer,
    )
