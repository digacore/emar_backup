import base64
from datetime import datetime, timedelta
from typing import List

import requests
from sqlalchemy import or_

from app import models as m
from app.logger import logger

from config import BaseConfig as CFG


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_html_body(location: m.Location, computers: list, alert_obj: m.Alert):

    image = open("app/static/favicon.ico", "rb")
    imgb = str(base64.b64encode(image.read()))[2:-1]
    image.close()

    computers_table = [
        f"<tr> <td>{comp.computer_name}</td> <td>{comp.location_name}</td> <td>{comp.last_time_online}</td> <td>{comp.last_download_time}</td> <td>{comp.folder_password}</td> <td>{comp.type}</td> </tr>"
        for comp in computers
    ]

    table_str = " ".join(computers_table)

    html_template = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <style>
                /* Add custom classes and styles that you want inlined here */
                </style>
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
            </head>
            <body class="bg-light">
                <div class="container">
                <div class="card my-10">
                    <div class="card-body">
                    <h1 class="h3 mb-2">Location {location.name} Alert - {alert_obj.name}</h1>
                    <h5 class="h3 mb-2" style="background-color: e74a3b;">Attention! All computers in this location have status RED!</h5>
                    <hr>
                    <div class="space-y-3">
                        <table class="table table-striped table-bordered table-hover model-list">
                            <thead>
                                <tr>
                                    <th>
                                        Computer
                                    </th>
                                    <th>
                                        Location
                                    </th>
                                    <th>
                                        Last time online
                                    </th>
                                    <th>
                                        Last download time
                                    </th>
                                    <th>
                                        Backup folder password
                                    </th>
                                    <th>
                                        Type
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_str}
                            </tbody>
                        </table>
                    </div>
                    <hr>
                        <p>
                        <img src="data:image/png;base64, {imgb}" alt="eMARVault" width="128px" height="128px">
                        </p>
                        <p>
                            support@digacore.com
                        </p>
                        <p>
                            732-646-5725
                        </p>
                    </div>
                </div>
                </div>
            </body>
        </html>
    """

    return html_template


# TODO remove this func if no use in future
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

        to_addresses = [user.email]
        html_body = get_html_body(computer, alert_obj)
        requests.post(
            CFG.MAIL_ALERTS,
            json={
                "alerted_target": computer.computer_name,
                "alert_status": alert_obj.alert_status,
                "from_email": alert_obj.from_email,
                "to_addresses": to_addresses,
                "subject": f"{computer.company_name} {computer.location_name} {alert_obj.name}",
                "body": "",
                "html_body": html_body,
            },
        )


def check_computer_send_mail(
    last_time: datetime,
    computer: m.Computer,
    alert_type: str,
    alert_obj: m.Alert,
    alerted_target=None,
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

    # if None - consider it as time was missed to keep status red
    last_online = (
        computer.last_time_online
        if computer
        else CFG.offset_to_est(datetime.utcnow(), True) - alerts_time * 2
    )
    last_download = (
        computer.last_download_time
        if computer
        else CFG.offset_to_est(datetime.utcnow(), True) - alerts_time * 2
    )
    # convert from str to datetime
    last_online = (
        datetime.strptime(last_online, TIME_FORMAT)
        if isinstance(last_online, str)
        else last_online
    )
    last_download = (
        datetime.strptime(last_download, TIME_FORMAT)
        if isinstance(last_download, str)
        else last_download
    )

    if not last_time and not computer and alerted_target:
        to_addresses: list = m.User.query.filter_by(asociated_with=alerted_target).all()
        alerted_computers: list = m.Computer.query.filter_by(
            location_name=alerted_target
        ).all()
        body = alert_obj.body if alert_obj.body else ""
        html_body = get_html_body(alerted_target, alerted_computers, alert_type)

        # TODO temporary to_addresses.extend(). Deside if to send mail to Global users

        requests.post(
            alert_url,
            json={
                "alerted_target": alerted_target,
                "alert_status": alert_obj.alert_status,
                "from_email": alert_obj.from_email,
                "to_addresses": to_addresses.extend(
                    ["xavrais312@gmail.com", "nberger@digacore.com"]
                ),
                "subject": alert_obj.subject,
                "body": "",
                "html_body": html_body,
            },
        )

        # TODO remove if overkill
        all_computers = m.Computer.query.filter_by(location_name=alerted_target).all()
        for computer in all_computers:
            computer.alert_status = f"red - {alert_type}"
            computer.update()
        logger.warning(
            "Location {} {} alert sent and alert statuses updated to red.",
            alerted_target,
            alert_type,
        )

    elif last_time < CFG.offset_to_est(datetime.now(), True) - alerts_time and (
        computer.alert_status == "green" or not computer.alert_status
    ):

        computer.alert_status = f"yellow - {alert_type}"
        computer.update()
        logger.warning(
            "Computer {} {} hours {} alert status updated to yellow.",
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
        logger.info(
            "Computer {} {} hours {} alert was already sent and updated.",
            computer.computer_name,
            alert_hours,
            alert_type,
        )


def time_type_check(time_obj):
    # last_download_time str check
    last_time = (
        datetime.strptime(time_obj, TIME_FORMAT)
        if isinstance(time_obj, str)
        else time_obj
    )
    return last_time


def check_and_alert():
    """
    CLI command for celery worker.
    Checks computers activity.
    Send email and change status if something went wrong.
    """
    locations: list[m.Location] = m.Location.query.all()
    # TODO update query to check computer last time inside database
    computers: list[m.Computer] = m.Computer.query.all()
    # TODO loop for all CUSTOM alerts to send email
    alerts: list[m.Alert] = m.Alert.query.all()

    alert_names = {alert.name: alert for alert in alerts}
    location_computers = {location.name: [] for location in locations}

    for computer in computers:
        location_computers[computer.location_name].append(computer)

    for location in location_computers:
        off_30_min_computers = 0
        no_update_files_2h = 0

        for computer in location_computers[location]:

            alert_types_computers = {
                "no_download_12h": computer.last_download_time,
                "offline_12h": computer.last_time_online,
            }

            last_download_time = time_type_check(computer.last_download_time)
            last_time_online = time_type_check(computer.last_time_online)

            # check alert_types and computers. Send email if computer outdated
            for alert_type in alert_types_computers:
                if alert_types_computers[alert_type] and alert_type in alert_names:
                    alert_obj: m.Alert = alert_names[alert_type]

                    # TODO apply something like this to DRY
                    # def handle_alert_case(last_time, alert_type, computer, alert_obj):
                    #     alerts_timedelta = {"offline_12h": 1800, "no_download_12h": 7200}

                    #     if last_time < CFG.offset_to_est(
                    #         datetime.now(), True
                    #     ) - timedelta(seconds=alerts_timedelta[alert_type]):

                    #         check_computer_send_mail(
                    #         last_time=last_time,
                    #         computer=computer,
                    #         alert_type=alert_type,
                    #         alert_obj=alert_obj,
                    #     )
                    #         return 1

                    # TODO find more elegant way to handle all cases
                    if last_time_online and alert_type == "offline_12h":
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

                    if last_download_time and alert_type == "no_download_12h":
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

        # check if all computer are yellow in every location. If yes - alert
        if off_30_min_computers == len(location_computers[location]):

            check_computer_send_mail(
                last_time=None,
                computer=None,
                alert_type="all offline 30 min",
                alert_obj=alert_names["all_offline"],
                alerted_target=location,
            )
            logger.warning(
                "All computers from location {} offline 30 min alert.", location
            )

        if no_update_files_2h == len(location_computers[location]):

            check_computer_send_mail(
                last_time=None,
                computer=None,
                alert_type="no new files 2 h",
                alert_obj=alert_names["no_files_2h"],
                alerted_target=location,
            )

            logger.warning("No new files over 2 h alert in location {}.", location)


def daily_summary():

    image = open("app/static/favicon.ico", "rb")
    imgb = str(base64.b64encode(image.read()))[2:-1]
    image.close()

    computers: list[m.Computer] = m.Computer.query.all()
    users: list[m.User] = m.User.query.all()

    # TODO what if we have multiple users in same company/location?
    email_user = {user.email: user for user in users}
    relation_user = {user.asociated_with: user.email for user in users}
    email_computers = {user.email: [] for user in users}

    for comp in computers:
        if comp.company_name in relation_user:
            email_computers[relation_user[comp.company_name]].append(comp)
        if comp.location_name in relation_user:
            email_computers[relation_user[comp.location_name]].append(comp)

    for user in users:
        if (
            user.asociated_with.lower() == "global-full"
            or user.asociated_with.lower() == "global-view"
        ):
            email_computers[user.email] = computers

    for recipient in email_computers:

        green_comp = len(
            [
                comp.alert_status
                for comp in email_computers[recipient]
                if "green" in comp.alert_status
            ]
        )
        yellow_comp = len(
            [
                comp.alert_status
                for comp in email_computers[recipient]
                if "yellow" in comp.alert_status
            ]
        )
        red_comp = len(
            [
                comp.alert_status
                for comp in email_computers[recipient]
                if "red" in comp.alert_status
            ]
        )

        computers_table = [
            f'<tr style="background-color: {get_status_color(comp.alert_status)};"> <td>{comp.computer_name}</td> <td>{comp.location_name}</td> <td>{comp.last_time_online}</td> <td>{comp.last_download_time}</td> <td>{comp.alert_status}</td> <td>{comp.type}</td> </tr>'
            for comp in email_computers[recipient]
        ]

        table_str = " ".join(computers_table)

        html_template = f"""
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
                </head>
                <body class="bg-light">
                    <div class="container">
                    <div class="card my-10">
                        <div class="card-body">
                        <h1 class="h3 mb-2">eMARVault daily summary for {email_user[recipient].asociated_with}</h1>
                        <hr>
                        <div class="space-y-3">

                            <table class="table table-striped table-bordered table-hover model-list">
                                <thead>
                                    <tr>
                                        <th>
                                            Green computers
                                        </th>
                                        <th>
                                            Yellow computers
                                        </th>
                                        <th>
                                            Red computers
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>
                                            {green_comp}
                                        </td>
                                        <td>
                                            {yellow_comp}
                                        </td>
                                        <td>
                                            {red_comp}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>

                            <hr>

                            <table class="table table-striped table-bordered table-hover model-list">
                                <thead>
                                    <tr>
                                        <th>
                                            Computer
                                        </th>
                                        <th>
                                            Location
                                        </th>
                                        <th>
                                            Last time online
                                        </th>
                                        <th>
                                            Last download time
                                        </th>
                                        <th>
                                            Alert status
                                        </th>
                                        <th>
                                            Type
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_str}
                                </tbody>
                            </table>
                        </div>

                        <hr>

                        <p>
                            <img src="data:image/png;base64, {imgb}" alt="eMARVault" width="128px" height="128px">
                        </p>
                        <p>
                            support@digacore.com
                        </p>
                        <p>
                            732-646-5725
                        </p>
                        </div>
                    </div>
                    </div>
                </body>
            </html>
        """.replace(
            "\n", ""
        )

        requests.post(
            CFG.MAIL_ALERTS,
            json={
                "alerted_target": "daily_summary",
                "alert_status": "daily_summary",
                "to_addresses": [recipient],
                "subject": f"eMARVault daily summary for {email_user[recipient].asociated_with}",
                "body": "",
                "html_body": html_template,
            },
        )


def get_status_color(alert_status):
    row_colors = {"green": "1cc88a", "yellow": "f6c23e", "red": "e74a3b"}
    for color in row_colors:
        if color in alert_status:
            return row_colors[color]


def reset_alert_statuses():
    """
    Set alert_status to green to all computers
    """
    computers: list[m.Computer] = m.Computer.query.all()

    for comp in computers:
        comp.alert_status = "green"
        comp.update()

    logger.debug("All computers alert_status updated to green")
