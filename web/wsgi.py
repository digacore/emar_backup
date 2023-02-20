#!/user/bin/env python
from datetime import datetime, timedelta
import requests
from app import create_app, db, models, forms
from app.logger import logger
from config import BaseConfig as CFG


app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, m=models, f=forms)


def check_computer_send_mail(
    last_time: datetime, computer: models.Computer, alert_type: str, alert_obj
):
    """Send email to support if last time online/download > alert_hours.
    If not - make status green
    Dont send repeatedly.

    Args:
        last_time (datetime): computer last time online/download
        computer (models.Computer): Computer model instance
        alert_type (str): alert type to log
        alert_obj (sqlalchemy.query): sqlalchemy.query object of some model
    """

    alert_url = CFG.MAIL_ALERTS

    alert_hours = 12
    alerts_time = timedelta(seconds=60 * 60 * alert_hours)

    if not last_time and not computer:
        requests.post(
            alert_url,
            json={
                "alerted_target": "all",
                "alert_status": alert_obj.alert_status,
                "from_email": alert_obj.from_email,
                "to_addresses": alert_obj.to_addresses,
                "subject": alert_obj.subject,
                "body": alert_obj.body,
                "html_body": alert_obj.html_body,
            },
        )

    elif last_time < datetime.now() - alerts_time and computer.alert_status != "red":
        requests.post(
            alert_url,
            json={
                "alerted_target": computer.computer_name,
                "alert_status": alert_obj.alert_status,
                # TODO Is from_email going to be configurable or take from BCG? Most likely yes
                "from_email": alert_obj.from_email,
                "to_addresses": alert_obj.to_addresses,
                "subject": f"{computer.computer_name} {alert_obj.subject}",
                "body": f"{computer.computer_name} {alert_obj.body}",
                "html_body": alert_obj.html_body,
            },
        )

        computer.alert_status = "red"
        computer.update()
        logger.warning(
            "Computer {} {} hours {} alert sent and alert status updated.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )
    elif last_time < datetime.now() - alerts_time and computer.alert_status == "red":
        # TODO think of which color means one alert and which means repited alerts for 1 comp
        computer.alert_status = "yellow"
        computer.update()
    elif last_time > datetime.now() - alerts_time:
        computer.alert_status = "green"
        computer.update()
    else:
        logger.info(
            "Computer {} {} hours {} alert was already sent and updated.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )


def alert_status_red(computers: list[models.Computer]):
    """Check if all current computers are red. If no - uppdate.
    If all red we don't send email again.

    Args:
        computers (list[models.Computer]): _description_

    Returns:
        int: quantity of red computers
    """

    all_red = 0
    for computer in computers:
        if computer.alert_status == "red":
            all_red += 1
        else:
            computer.alert_status = "red"
            computer.update()
    return all_red


@app.cli.command()
def check_and_alert():
    """
    CLI command for celery worker.
    Checks computers activity.
    Send email and change status if something went wrong.
    """
    computers: list[models.Computer] = models.Computer.query.all()
    # TODO loop for all CUSTOM alerts to send email
    alerts: list[models.Alert] = models.Alert.query.all()
    alert_names = [i.name for i in alerts]
    time_format = "%Y-%m-%d %H:%M:%S"

    off_30_min_computers = 0
    no_update_files_2h = 0

    for computer in computers:

        # check last_download_time
        if computer.last_download_time and "no_download_12h" in alert_names:
            no_download_12h: models.Alert = models.Alert.query.filter_by(
                name="no_download_12h"
            ).first()
            last_download_time = (
                datetime.strptime(computer.last_download_time, time_format)
                if isinstance(computer.last_download_time, str)
                else computer.last_download_time
            )

            check_computer_send_mail(
                last_time=last_download_time,
                computer=computer,
                alert_type="download",
                alert_obj=no_download_12h,
            )

            if last_download_time < datetime.now() - timedelta(seconds=7200):
                no_update_files_2h += 1

        # check last_time_online
        if computer.last_time_online and "offline_12h" in alert_names:
            offline_12h: models.Alert = models.Alert.query.filter_by(
                name="offline_12h"
            ).first()
            last_time_online = (
                datetime.strptime(computer.last_time_online, time_format)
                if isinstance(computer.last_time_online, str)
                else computer.last_time_online
            )

            check_computer_send_mail(
                last_time=last_download_time,
                computer=computer,
                alert_type="offline",
                alert_obj=offline_12h,
            )

            if last_time_online < datetime.now() - timedelta(seconds=1800):
                off_30_min_computers += 1

    if off_30_min_computers == len(computers):
        logger.warning("All computers offline 30 min alert.")

        if alert_status_red(computers) != len(computers):
            all_offline: models.Alert = (
                models.Alert.query.filter_by(name="all_offline").first()
                if "all_offline" in alert_names
                else None
            )
            check_computer_send_mail(
                last_time=None, computer=None, alert_type="", alert_obj=all_offline
            )
            logger.warning(
                "All computers offline 30 min alert sent and alert statuses updated."
            )

    if no_update_files_2h == len(computers):
        logger.warning("No new files over 2 h alert.")

        if alert_status_red(computers) != len(computers):
            no_files_2h: models.Alert = (
                models.Alert.query.filter_by(name="no_files_2h").first()
                if "no_files_2h" in alert_names
                else None
            )
            check_computer_send_mail(
                last_time=None, computer=None, alert_type="", alert_obj=no_files_2h
            )

            logger.info("No new files over 2 h alert sent and alert statuses updated.")


@app.cli.command()
def create_superuser():
    user = models.User(
        username="emarsuperuser",
        email="emarsup@email.com",
        password=CFG.SUPERPASS,
        asociated_with="global-full",
    )
    user.save()
    logger.info("Superuser created")


if __name__ == "__main__":
    app.run()
