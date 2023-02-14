#!/user/bin/env python
from datetime import datetime, timedelta
import requests
from app import create_app, db, models, forms
from app.logger import logger
from config import BaseConfig as BCG


app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, m=models, f=forms)


def send_mail(
    last_time: datetime,
    alert_status: str,
    subject: str,
    body: str,
    html_body: str,
    computer: models.Computer,
    alert_type:str):
    """Send email to support if last time online/download > alert_hours.
    If not - make status green
    Dont send repeatedly.

    Args:
        last_time (datetime): computer last time online/download
        alert_status (str): green or red
        subject (str): email subject
        body (str): email body
        html_body (str): email html styled body
        computer (models.Computer): Computer model instance
        alert_type (str): alert type to log
    """

    alert_url = BCG.MAIL_ALERTS
    from_email = BCG.SUPPORT_EMAIL
    to_addresses = BCG.TO_ADDRESSES

    alert_hours = 12
    alerts_time = timedelta(seconds=60*60*alert_hours)

    if last_time < datetime.now() - alerts_time and computer.alert_status != "red":
        requests.post(alert_url, json={
            "alerted_target": computer.computer_name,
            "alert_status": alert_status,
            "from_email": from_email,
            "to_addresses": to_addresses,
            "subject": subject,
            "body": body,
            "html_body": html_body
            })

        computer.alert_status = "red"
        computer.update()
        logger.warning("Computer {} {} hours {} alert sent and alert status updated.", computer.computer_name, alert_hours, alert_type)
    elif last_time > datetime.now() - alerts_time:
        computer.alert_status = "green"
        computer.update()
    else:
        logger.info("Computer {} {} hours {} alert was already sent and updated.", computer.computer_name, alert_hours, alert_type)


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
    alert_url = BCG.MAIL_ALERTS
    time_format = "%Y-%m-%d %H:%M:%S"
    from_email = BCG.SUPPORT_EMAIL
    to_addresses = BCG.TO_ADDRESSES

    off_30_min_computers = 0
    no_update_files_2h = 0

    for computer in computers:

        # check last_download_time
        if computer.last_download_time:
            last_download_time = datetime.strptime(computer.last_download_time, time_format) if \
                isinstance(computer.last_download_time, str) else computer.last_download_time

            send_mail(
                last_time=last_download_time,
                alert_status="red",
                subject=f"Computer {computer.computer_name} 12 hours alert!",
                body=f"Computer {computer.computer_name} had not download files for more then 12 hours.",
                html_body="",
                computer=computer,
                alert_type="download"
                )

            if last_download_time < datetime.now() - timedelta(seconds=7200):
                no_update_files_2h += 1

        # check last_time_online
        if computer.last_time_online:
            last_time_online = datetime.strptime(computer.last_time_online, time_format) if \
                isinstance(computer.last_time_online, str) else computer.last_time_online

            send_mail(
                last_time=last_time_online,
                alert_status="red",
                subject=f"Computer {computer.computer_name} 12 hours offline alert!",
                body=f"Computer {computer.computer_name} had been offline for more then 12 hours.",
                html_body="",
                computer=computer,
                alert_type="offline"
                )

            if last_time_online < datetime.now() - timedelta(seconds=1800):
                off_30_min_computers += 1

    if off_30_min_computers == len(computers):
        logger.warning("All computers offline 30 min alert.")

        if alert_status_red(computers) != len(computers):
            requests.post(alert_url, json={
                "alerted_target": "all",
                "alert_status": "red",
                "from_email": from_email,
                "to_addresses": to_addresses,
                "subject": "All computers offline 30 min alert!",
                "body": "All computers are offline more then 30 minutes.",
                "html_body": ""
                })

        logger.warning("All computers offline 30 min alert sents and alert statuses updated.")

    if no_update_files_2h == len(computers):
        logger.warning("No new files over 2 h alert.")

        if alert_status_red(computers) != len(computers):
            requests.post(alert_url, json={
                "alerted_target": "all",
                "alert_status": "red",
                "from_email": from_email,
                "to_addresses": to_addresses,
                "subject": "No new files over 2 h alert!",
                "body": "No new files were downloaded by all computers for over 2 hours.",
                "html_body": ""
                })

        logger.info("No new files over 2 h alert sent and alert statuses updated.")


@app.cli.command()
def create_superuser():
    user = models.User(
            username="emarsuperuser",
            email="emarsup@email.com",
            password=BCG.SUPERPASS,
        )
    user.save()
    logger.info("Superuser created")

if __name__ == "__main__":
    app.run()
