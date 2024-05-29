import os
import subprocess

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from redbeat import RedBeatSchedulerEntry

from app.logger import logger

import celery_config


load_dotenv()

REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_ADDR = os.environ.get("REDIS_ADDR", f"localhost:{REDIS_PORT}")
BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_ADDR}"


app = Celery(__name__)
app.conf.broker_url = BROKER_URL
app.conf.timezone = "US/Eastern"
app.conf.redbeat_redis_url = f"{BROKER_URL}/1"
app.config_from_object(celery_config)
# celery.conf.result_backend = conf.REDIS_URL_FOR_CELERY


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Critical alert when location offline - run every hour
    # interval = crontab(minute=0)
    # entry = RedBeatSchedulerEntry(
    #     "critical_alert_email", "worker.critical_alert_email", interval, app=app
    # )
    # entry.save()

    # Alert when primary computer is down - run every hour
    # interval = crontab(minute=0)
    # entry = RedBeatSchedulerEntry(
    #     "primary_computer_alert_email",
    #     "worker.primary_computer_alert_email",
    #     interval,
    #     app=app,
    # )
    # entry.save()

    # Send daily summary - run every day at 11:00 AM (EST)
    # interval = crontab(hour=11, minute=0)
    # entry = RedBeatSchedulerEntry(
    #     "daily_summary_email", "worker.daily_summary_email", interval, app=app
    # )
    # entry.save()

    # Send weekly summary - run every Monday at 11:00 AM (EST)
    interval = crontab(hour=11, minute=0, day_of_week="mon")
    entry = RedBeatSchedulerEntry(
        "weekly_summary_email", "worker.weekly_summary_email", interval, app=app
    )
    entry.save()

    # Update Company/Location statistics and Location status - run every 5 minutes
    interval = crontab(minute="*/5")
    entry = RedBeatSchedulerEntry(
        "update_cl_stat", "worker.update_cl_stat", interval, app=app
    )
    entry.save()

    # Clean old logs every midnight
    interval = crontab(hour=0, minute=0)
    entry = RedBeatSchedulerEntry(
        "clean_old_logs", "worker.clean_old_logs", interval, app=app
    )
    entry.save()

    logger.debug("Tasks added to Redis")


# @app.task
# def critical_alert_email():
#     flask_proc = subprocess.Popen(["flask", "critical-alert-email"])
#     flask_proc.communicate()


# @app.task
# def primary_computer_alert_email():
#     flask_proc = subprocess.Popen(["flask", "primary-computer-alert-email"])
#     flask_proc.communicate()


# @app.task
# def daily_summary_email():
#     flask_proc = subprocess.Popen(["flask", "daily-summary-email"])
#     flask_proc.communicate()


@app.task
def weekly_summary_email():
    flask_proc = subprocess.Popen(["flask", "weekly-summary-email"])
    flask_proc.communicate()


@app.task
def update_cl_stat():
    flask_proc = subprocess.Popen(["flask", "update-cl-stat"])
    flask_proc.communicate()


@app.task
def clean_old_logs():
    flask_proc = subprocess.Popen(["flask", "clean-old-logs"])
    flask_proc.communicate()


@app.task
def scan_pcc_activations(scan_record_id: int):
    flask_proc = subprocess.Popen(
        ["flask", "scan-pcc-activations", str(scan_record_id)]
    )
    flask_proc.communicate()
