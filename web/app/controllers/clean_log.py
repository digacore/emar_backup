from datetime import datetime, timedelta

from app import models as m, db
from config import BaseConfig as CFG
from app.logger import logger


def clean_old_logs():
    """
    Clean old computer logs, system logs and log_events from database
    """
    # Clean old system logs
    old_system_logs_query = db.session.query(m.SystemLog).filter(
        m.SystemLog.created_at
        < datetime.utcnow() - timedelta(days=CFG.SYSTEM_LOGS_DELETION_PERIOD)
    )
    old_system_logs_amount = len(old_system_logs_query.all())
    old_system_logs_query.delete()

    # Clean old computer logs
    old_computer_logs_query = db.session.query(m.BackupLog).filter(
        m.BackupLog.end_time
        < datetime.utcnow() - timedelta(days=CFG.COMPUTER_LOGS_DELETION_PERIOD)
    )
    old_computer_logs_amount = len(old_computer_logs_query.all())
    old_computer_logs_query.delete()

    # Clean old log events
    old_log_events_query = db.session.query(m.LogEvent).filter(
        m.LogEvent.created_at
        < datetime.utcnow() - timedelta(days=CFG.LOG_EVENT_DELETION_PERIOD)
    )
    old_log_events_amount = len(old_log_events_query.all())
    old_log_events_query.delete()

    db.session.commit()

    logger.info(
        "<Old system logs [{}]; old computer logs [{}] old log events [{}] were deleted>",
        old_system_logs_amount,
        old_computer_logs_amount,
        old_log_events_amount,
    )
