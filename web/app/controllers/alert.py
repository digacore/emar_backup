from datetime import datetime, timedelta
from typing import List

import requests
from sqlalchemy import or_

from app import models as m
from app.logger import logger

from config import BaseConfig as CFG


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def alert_additional_users(computer: m.Computer, alert_obj: m.Alert):
    # get users associated with this computer
    users: List[m.User] = m.User.query.filter(
        or_(
            m.User.asociated_with == computer.company_name,
            m.User.asociated_with == computer.location_name,
        )
    ).all()

    for user in users:
        if alert_obj.name not in [alert.name for alert in user.alerts]:
            # if user does not have this alert_obj in his alerts
            continue

        logger.debug(
            "Sending additional email to user {} with {} alert",
            user.username,
            alert_obj.name,
        )

        to_addresses = user.email
        requests.post(
            CFG.MAIL_ALERTS,
            json={
                "alerted_target": computer.computer_name,
                "alert_status": alert_obj.alert_status,
                "from_email": alert_obj.from_email,
                "to_addresses": to_addresses,
                "subject": f"{computer.computer_name} {alert_obj.subject}",
                "body": f"{computer.computer_name} {alert_obj.body}",
                "html_body": alert_obj.html_body,
            },
        )


def check_computer_send_mail(
    last_time: datetime, computer: m.Computer, alert_type: str, alert_obj
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

    alert_hours: int = 12
    alerts_time = timedelta(seconds=60 * 60 * alert_hours)

    # TODO find more elegant way to handle all cases
    # convert from str to datetime
    last_online = (
        datetime.strptime(computer.last_time_online, TIME_FORMAT)
        if isinstance(computer.last_time_online, str)
        else computer.last_time_online
    )
    last_download = (
        datetime.strptime(computer.last_download_time, TIME_FORMAT)
        if isinstance(computer.last_download_time, str)
        else computer.last_download_time
    )
    # if None - consider it as time was missed to keep status red
    last_online = (
        last_online
        if last_online
        else CFG.offset_to_est(datetime.now(), True) - alerts_time * 2
    )
    last_download = (
        last_download
        if last_download
        else CFG.offset_to_est(datetime.now(), True) - alerts_time * 2
    )

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

        all_computers = m.Computer.query.all()
        for computer in all_computers:
            computer.alert_status = f"red - {alert_type}"
            computer.update()
        logger.warning(
            "Computer {} {} hours {} alert sent and alert status updated to red.",
            "ALL",
            "null",
            alert_type,
        )

    elif (
        last_time < CFG.offset_to_est(datetime.now(), True) - alerts_time
        and computer.alert_status == "green"
    ):
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
        alert_additional_users(computer, alert_obj)

        computer.alert_status = f"yellow - {alert_type}"
        computer.update()
        logger.warning(
            "Computer {} {} hours {} alert sent and alert status updated to yellow.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )
    elif (
        last_time < CFG.offset_to_est(datetime.now(), True) - alerts_time
        and computer.alert_status == "yellow"
    ):
        computer.alert_status = f"red - {alert_type}"
        computer.update()
        logger.warning(
            "Computer {} {} hours {} alert status updated to red due to repeated yellow condition.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )
    elif (
        last_download > CFG.offset_to_est(datetime.now(), True) - alerts_time
        and last_online > CFG.offset_to_est(datetime.now(), True) - alerts_time
    ):
        computer.alert_status = "green"
        computer.update()
        logger.info(
            "Computer {} {} hours {} alert status updated to green.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )
    else:
        computer.alert_status = f"red - {alert_type}"
        computer.update()
        logger.info(
            "Computer {} {} hours {} alert was already sent and updated.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )


def alert_status_red(computers: list[m.Computer]):
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


def check_and_alert():
    """
    CLI command for celery worker.
    Checks computers activity.
    Send email and change status if something went wrong.
    """
    computers: list[m.Computer] = m.Computer.query.all()
    # TODO loop for all CUSTOM alerts to send email
    alerts: list[m.Alert] = m.Alert.query.all()
    alert_names = [i.name for i in alerts]

    off_30_min_computers = 0
    no_update_files_2h = 0

    for computer in computers:

        alert_types_computers = {
            "no_download_12h": computer.last_download_time,
            "offline_12h": computer.last_time_online,
        }

        # last_download_time str check
        last_download_time = (
            datetime.strptime(computer.last_download_time, TIME_FORMAT)
            if isinstance(computer.last_download_time, str)
            else computer.last_download_time
        )

        # last_time_online str check
        last_time_online = (
            datetime.strptime(computer.last_time_online, TIME_FORMAT)
            if isinstance(computer.last_time_online, str)
            else computer.last_time_online
        )

        # check alert_types and computers. Send email if computer outdated
        for alert_type in alert_types_computers:
            if alert_types_computers[alert_type] and alert_type in alert_names:
                alert_obj: m.Alert = m.Alert.query.filter_by(name=alert_type).first()

                # TODO find more elegant way to handle all cases
                if last_time_online:
                    if last_time_online < CFG.offset_to_est(
                        datetime.now(), True
                    ) - timedelta(seconds=1800):
                        off_30_min_computers += 1

                    check_computer_send_mail(
                        last_time=last_time_online,
                        computer=computer,
                        alert_type=alert_type,
                        alert_obj=alert_obj,
                    )

                if last_download_time:
                    if last_download_time < CFG.offset_to_est(
                        datetime.now(), True
                    ) - timedelta(seconds=7200):
                        no_update_files_2h += 1

                    check_computer_send_mail(
                        last_time=last_download_time,
                        computer=computer,
                        alert_type=alert_type,
                        alert_obj=alert_obj,
                    )

    if off_30_min_computers == len(computers):
        logger.warning("All computers offline 30 min alert.")

        if alert_status_red(computers) != len(computers):
            all_offline: m.Alert = (
                m.Alert.query.filter_by(name="all_offline").first()
                if "all_offline" in alert_names
                else None
            )
            check_computer_send_mail(
                last_time=None,
                computer=None,
                alert_type="all offline 30 min",
                alert_obj=all_offline,
            )
            logger.warning(
                "All computers offline 30 min alert sent and alert statuses updated."
            )

    if no_update_files_2h == len(computers):
        logger.warning("No new files over 2 h alert.")

        if alert_status_red(computers) != len(computers):
            no_files_2h: m.Alert = (
                m.Alert.query.filter_by(name="no_files_2h").first()
                if "no_files_2h" in alert_names
                else None
            )
            check_computer_send_mail(
                last_time=None,
                computer=None,
                alert_type="no new files 2 h",
                alert_obj=no_files_2h,
            )

            logger.info("No new files over 2 h alert sent and alert statuses updated.")
