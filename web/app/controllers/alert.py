# import base64
from datetime import datetime, timedelta

import requests
from sqlalchemy import or_

from app import models as m
from app.logger import logger

from config import BaseConfig as CFG

from pprint import pprint

from .log_event import create_log_event


def get_timedelta_hours(hours: int) -> datetime:
    """Get datetime to calculate time when compering with computer last_time

    Args:
        hours (int): Hours after which alert should be sned

    Returns:
        datetime: datetime for comparison with computer last_time
    """
    alerts_timedelta = timedelta(seconds=60 * 60 * hours)

    return CFG.offset_to_est(datetime.utcnow(), True) - alerts_timedelta


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
OFFLINE_ALERT_12H: datetime = get_timedelta_hours(12)
NO_DOWNLOAD_ALERT_4H: datetime = get_timedelta_hours(4)
LOCATION_OFFLINE_30MIN: datetime = get_timedelta_hours(0.5)
LOCATION_OFFLINE_30MIN_IN_SEC: int = 1800
LOCATION_NO_DOWNLOAD_3H: datetime = get_timedelta_hours(3)
LOCATION_NO_DOWNLOAD_3H_IN_SEC: int = 10800


def get_html_body(
    location: str,
    computers: list,
    alert_details: str,
    attention: str = "Attention! All computers in this location have status RED!",
) -> str:

    # TODO remove if unused
    # image = open("app/static/favicon.ico", "rb")
    # imgb = str(base64.b64encode(image.read()))[2:-1]
    # image.close()

    attention_color = "#e74a3b" if "RED" in attention else "#1cc88a"

    computers_table = [
        f"<tr> <td>{comp.computer_name}</td> <td>{comp.location_name}</td> <td>{comp.last_time_online}</td>\
            <td>{comp.last_download_time}</td> <td>{comp.folder_password}</td> <td>{comp.device_role.capitalize()}</td> </tr>"
        for comp in computers
    ]

    table_str = " ".join(computers_table)
    styles = """
        table {
        font-family: arial, sans-serif;
        border-colapse: collapse;
        width: 100%;
        }

        td, th {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 8px;
        }

        tr:nth-child(even) {
        background-color: #dddddd;
        }
    """

    # base64 png image
    # <img src="data:image/png;base64, {imgb}" alt="eMARVault" width="128px" height="128px">
    # TODO do something with this html template to make it universal both for daily summary and alerts

    # TODO put new instructions above contact when supplied
    # old one:
    # <hr style="margin-left: 10%;margin-right: 10%;">
    # <h1 style="text-align:center">Instructions on how to access the eMARVault backups</h1>
    # <img src="https://user-images.githubusercontent.com/54449043/234306932-37cde083-9c8b-4eab-a12b-5ef393680ae2.png">

    html_template = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <style>
                {styles}
                </style>
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
            </head>
            <body class="bg-light">
                <div class="container">
                <div class="card my-10">
                    <div class="card-body">
                    <h1 class="h3 mb-2" style="text-align: center">Location {location} Alert - {alert_details}</h1>
                    <h4 class="h3 mb-2" style="background-color: {attention_color}; text-align: center"
                    >{attention}</h4>

                    <hr style="margin-left: 10%;margin-right: 10%;">

                    <div class="space-y-3">
                        <table class="table table-striped table-bordered table-hover model-list"
                        style="border-collapse: collapse;"
                        >
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

                    <hr style="margin-left: 10%;margin-right: 10%;">

                        <p>
                        <a href="https://emarvault.com/">
                            <img src="https://emarvault.com/static//img/emar_icon_web.jpg" alt="eMARVault" width="128px" height="128px">
                        </a>
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


def send_alert_email(
    alerted_target: str, alert_obj: m.Alert, status_details: str, attention=None
) -> bool:
    """Send all red or all green email to appropriate user

    Args:
        alerted_target (str): location name
        alert_obj (m.Alert): Alert sqla object
        status_details (str): description of alert status and it's change

    Returns:
        bool: return true to confrim that request was sent
    """
    # query for alerted location to get location company name
    alerted_location: m.Location = m.Location.query.filter_by(
        name=alerted_target
    ).first()

    # query for users who are associated with alerted location/company
    alerted_users: list[m.User] = m.User.query.filter(
        or_(
            m.User.asociated_with == alerted_location.company_name,
            m.User.asociated_with == alerted_location.name,
        )
    ).all()

    to_addresses = [user.email for user in alerted_users]

    # query for computers in alerted location
    alerted_computers: list = m.Computer.query.filter_by(
        location_name=alerted_target
    ).all()
    # TODO remove if unused
    # body = alert_obj.body if alert_obj.body else ""
    html_body = (
        get_html_body(alerted_target, alerted_computers, status_details, attention)
        if attention
        else get_html_body(alerted_target, alerted_computers, status_details)
    )

    # TODO temporary to_addresses. Remove in future
    request_json = {
        "alerted_target": alerted_target,
        "alert_status": alert_obj.alert_status,
        "from_email": alert_obj.from_email,
        "to_addresses": [CFG.DEV_EMAIL, CFG.CLIENT_EMAIL],
        "subject": alert_obj.subject,
        "body": "",
        "html_body": html_body,
    }
    pprint(request_json)

    # TODO Deside if to send mail to Global users
    requests.post(
        CFG.MAIL_ALERTS,
        json=request_json,
    )

    # return true to confrim that request was sent
    return True


def check_computer_send_mail(
    last_time: datetime,
    compare_time: datetime,
    computer: m.Computer,
    alert_type: str,
    alert_obj: m.Alert,
    alerted_target: str = None,
):
    """
    Send email to support if last time online/download > alert_hours.
    If not - make status green
    Dont send repeatedly.

    Args:
        last_time (datetime): computer last time online/download
        compare_time (datetime): time limit to which computer last times would be compared
        computer (models.Computer): Computer model instance
        alert_type (str): alert type to log
        alert_obj (sqlalchemy.query): sqlalchemy.query object of some model
        alerted_target (str): alerted location name when all offline or no backup. Defaults to None.
    """

    alert_url = CFG.MAIL_ALERTS

    # put computer alerts time into dict for ease checks of its type
    last_tms = {
        "last_online": time_type_check(computer, "online"),
        "last_download": time_type_check(computer, "download"),
    }

    logger.debug(
        "{} -> utc: {}, est: {} compare download 4: {} > {} = {};\n compare online 12: \
        {} > {} = {};\n compare no download 3: {} < {} = {};\n compare offline 30 min: {} < {} = {};\n",
        computer,
        datetime.utcnow(),
        CFG.offset_to_est(datetime.utcnow(), True),
        last_tms["last_download"].strftime("%Y-%m-%d %H:%M:%S"),
        NO_DOWNLOAD_ALERT_4H,
        last_tms["last_download"] > NO_DOWNLOAD_ALERT_4H,
        last_tms["last_online"].strftime("%Y-%m-%d %H:%M:%S"),
        OFFLINE_ALERT_12H,
        last_tms["last_online"] > OFFLINE_ALERT_12H,
        last_tms["last_download"].strftime("%Y-%m-%d %H:%M:%S"),
        LOCATION_NO_DOWNLOAD_3H,
        last_tms["last_download"] < LOCATION_NO_DOWNLOAD_3H,
        last_tms["last_online"].strftime("%Y-%m-%d %H:%M:%S"),
        LOCATION_OFFLINE_30MIN,
        last_tms["last_online"] < LOCATION_OFFLINE_30MIN,
    )

    if not last_time and not computer and alerted_target:
        # query for all computers in location
        alerted_computers: list[m.Computer] = m.Computer.query.filter_by(
            location_name=alerted_target
        ).all()

        # check for red before computers update
        all_red = check_for_red(alerted_computers)

        # decide which alert details assign to location's computers alert_status and update them
        for computer in alerted_computers:
            if "offline" in alert_type:
                # get hours offline of no download from (EST now time - last download/online)
                time_diff = (
                    get_timedelta_hours(0) - time_type_check(computer, "online")
                ).total_seconds() / 3600
                time_diff = "30 min" if time_diff < 1 else f"{round(time_diff)} h"
                status_details = f"offline over {time_diff}"
            else:
                time_diff = round(
                    (
                        get_timedelta_hours(0) - time_type_check(computer, "download")
                    ).total_seconds()
                    / 3600
                )
                status_details = f"no backup over {time_diff} h"
            computer.alert_status = f"red - {status_details}"
            computer.update()

            if computer.logs_enabled:
                create_log_event(computer, m.LogType.STATUS_RED, data=status_details)

            logger.debug(
                "Computer {} from location {} has alert_status {}",
                computer.computer_name,
                computer.location_name,
                computer.alert_status,
            )

        # if all computer are already red - quit from this func
        if all_red:
            logger.debug(
                "Location - {} alert - {} was already sent and updated. All red.",
                alerted_target,
                alert_type,
            )
            return

        # query for alerted location to get location company name
        alerted_location: m.Location = m.Location.query.filter_by(
            name=alerted_target
        ).first()

        # query for users who are associated with alerted location/company
        alerted_users: list[m.User] = m.User.query.filter(
            or_(
                m.User.asociated_with == alerted_location.company_name,
                m.User.asociated_with == alerted_location.name,
            )
        ).all()

        to_addresses = [user.email for user in alerted_users]

        # TODO remove if unused
        # body = alert_obj.body if alert_obj.body else ""
        html_body = get_html_body(alerted_target, alerted_computers, status_details)

        # TODO temporary to_addresses. Remove in future
        request_json = {
            "alerted_target": alerted_target,
            "alert_status": alert_obj.alert_status,
            "from_email": alert_obj.from_email,
            "to_addresses": [CFG.DEV_EMAIL, CFG.CLIENT_EMAIL],
            "subject": alert_obj.subject,
            "body": "",
            "html_body": html_body,
        }
        pprint(request_json)

        # TODO Deside if to send mail to Global users
        requests.post(
            alert_url,
            json=request_json,
        )

        logger.warning(
            "Location {} {} alert sent and alert statuses updated to red.",
            alerted_target,
            alert_type,
        )

    # elif last_time < compare_time and computer.alert_status != "yellow":
    elif last_time < compare_time:
        # if computer did not download files or was offline for alerts_time
        # assign status yellow or just update it's hours

        current_location: m.Location = m.Location.query.filter_by(
            name=computer.location_name
        ).first()
        current_location_comps: list[m.Computer] = m.Computer.query.filter_by(
            location=current_location
        ).all()

        # do not update to yellow if all computers in location are red
        if check_for_red(
            current_location_comps,
        ):
            logger.debug(
                "Computer - {} alert status - {}. all computers in location are red",
                computer.computer_name,
                computer.alert_status,
            )
            return

        # gent hours offline of no download from (EST now time - last download/online)
        time_diff = round((get_timedelta_hours(0) - last_time).total_seconds() / 3600)
        status_details = (
            f"offline over {time_diff} h"
            if "offline" in alert_type
            else f"online but no backup over {time_diff} h"
        )

        # if computer status is something like "red - ip_blacklisted" - keep it red until it becomes green
        if computer.alert_status in CFG.SPECIAL_STATUSES:
            logger.info(
                "Computer - {} alert status - {}.",
                computer.computer_name,
                computer.alert_status,
            )
            return

        computer.alert_status = f"yellow - {status_details}"
        computer.update()

        if computer.logs_enabled:
            create_log_event(computer, m.LogType.STATUS_YELLOW, data=status_details)

        logger.warning(
            "Computer - {} alert - {} status updated to yellow.",
            computer.computer_name,
            status_details,
        )
    elif (
        last_tms["last_download"] > NO_DOWNLOAD_ALERT_4H
        and last_tms["last_online"] > OFFLINE_ALERT_12H
    ):

        current_location_comps = m.Computer.query.filter_by(
            location_name=computer.location_name
        ).count()

        # if (comp has no download 3h OR is offline 30 min) AND it is only one in his location - keep it red
        if (
            last_tms["last_download"] <= LOCATION_NO_DOWNLOAD_3H
            or last_tms["last_online"] <= LOCATION_OFFLINE_30MIN
        ) and current_location_comps <= 1:
            logger.info(
                "Computer - {} alert status - {}.",
                computer.computer_name,
                computer.alert_status,
            )
            return

        # if computer status is something like "red - ip_blacklisted" - keep it red until it becomes green
        if computer.alert_status in CFG.SPECIAL_STATUSES:
            logger.info(
                "Computer - {} alert status - {}.",
                computer.computer_name,
                computer.alert_status,
            )
            return

        # TODO: change status on green when successful download happened
        computer.alert_status = "green"
        computer.update()

        if computer.logs_enabled:
            create_log_event(computer, m.LogType.STATUS_GREEN)

        logger.info(
            "Computer - {} alert - {} status updated to green.",
            computer.computer_name,
            alert_type,
        )
    else:
        logger.info(
            "Computer - {} alert - {} was already sent and updated.",
            computer.computer_name,
            alert_type,
        )


def time_type_check(computer: m.Computer, return_val: str) -> datetime:
    """
    Check and transform computer last_time_online and last_download_time
    to datetime objects, if it is string. If it is non - meaning field is empty -
    consider time was missed

    Args:
        computer (m.Computer): sqla Computer object
        return_val (str): marker to undestand which value to return

    Raises:
        ValueError: raise error if return_val is not existent

    Returns:
        datetime: datetime obj to determine if computer is offline/no download
    """

    # if None - consider it as time was missed to keep status red
    late_time = get_timedelta_hours(999)

    last_tms = {
        "last_online": 0,
        "last_download": 0,
    }

    if computer:
        last_tms["last_online"] = computer.last_time_online
        last_tms["last_download"] = computer.last_download_time

        for ls_tm in last_tms:
            if last_tms[ls_tm]:
                # convert str to datetime or return same obj if type is already datetime
                last_tms[ls_tm] = (
                    datetime.strptime(last_tms[ls_tm], TIME_FORMAT)
                    if isinstance(last_tms[ls_tm], str)
                    else last_tms[ls_tm]
                )
            else:
                # assign late_time if last_tms[ls_tm] is None
                last_tms[ls_tm] = late_time

    else:
        last_tms["last_online"] = late_time
        last_tms["last_download"] = late_time

    if return_val == "online":
        return last_tms["last_online"]
    elif return_val == "download":
        return last_tms["last_download"]
    else:
        raise ValueError("Incorrect return_val arg for time_type_check()")


def check_and_alert():
    """
    CLI command for celery worker.
    Checks computers activity.
    Send email and change status.
    """

    locations: list[m.Location] = m.Location.query.all()
    # TODO update query to check computer last time inside database
    computers: list[m.Computer] = m.Computer.query.all()
    # TODO loop for all CUSTOM alerts to send email
    alerts: list[m.Alert] = m.Alert.query.all()
    # take all_green alert from alerts list to no query again
    all_green_li = [alert for alert in alerts if alert.name == "all_green"]

    alert_names = {alert.name: alert for alert in alerts}
    location_computers = {location.name: [] for location in locations}

    # add computers to locations. Add dummy location for computers with empty location
    no_location = "no_location"
    location_computers[no_location] = []
    for computer in computers:
        if computer.location_name:
            location_computers[computer.location_name].append(computer)
        else:
            location_computers[no_location].append(computer)

    for location in location_computers:
        # do nothing if no computer in location
        if len(location_computers[location]) == 0:
            continue

        off_time_computers = 0
        no_update_files_time = 0

        red_comps = [
            comp
            for comp in location_computers[location]
            if "red" in str(comp.alert_status)
        ]

        for computer in location_computers[location]:

            last_download_time = time_type_check(computer, "download")
            last_time_online = time_type_check(computer, "online")

            alert_types_computers = {
                "no_download_4h": last_download_time,
                "offline_12h": last_time_online,
            }

            # check alert_types and computers. Send email if computer outdated
            for alert_type in alert_types_computers:
                if alert_types_computers[alert_type] and alert_type in alert_names:
                    alert_obj: m.Alert = alert_names[alert_type]

                    # TODO apply something like this to DRY
                    # def handle_alert_case(last_time, alert_type, computer, alert_obj):
                    #     alerts_timedelta = {"offline_12h": LOCATION_OFFLINE_30MIN_IN_SEC, "no_download_4h": LOCATION_NO_DOWNLOAD_3H_IN_SEC}

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

                    if last_download_time and "no_download" in alert_type:
                        if last_download_time < CFG.offset_to_est(
                            datetime.utcnow(), True
                        ) - timedelta(seconds=LOCATION_NO_DOWNLOAD_3H_IN_SEC):
                            no_update_files_time += 1

                        check_computer_send_mail(
                            last_time=last_download_time,
                            compare_time=NO_DOWNLOAD_ALERT_4H,
                            computer=computer,
                            alert_type=alert_type,
                            alert_obj=alert_obj,
                        )

                    if last_time_online and "offline" in alert_type:
                        if last_time_online < CFG.offset_to_est(
                            datetime.utcnow(), True
                        ) - timedelta(seconds=LOCATION_OFFLINE_30MIN_IN_SEC):
                            off_time_computers += 1

                        check_computer_send_mail(
                            last_time=last_time_online,
                            compare_time=OFFLINE_ALERT_12H,
                            computer=computer,
                            alert_type=alert_type,
                            alert_obj=alert_obj,
                        )

        # if computer is without location, don't send any email for location
        if location == no_location:
            continue

        if no_update_files_time == len(location_computers[location]):

            check_computer_send_mail(
                last_time=None,
                compare_time=LOCATION_NO_DOWNLOAD_3H,
                computer=None,
                alert_type="no new files 3 h",
                alert_obj=alert_names["no_files_3h"],
                alerted_target=location,
            )

            logger.warning("No new files over 3 h alert in location {}.", location)

        if off_time_computers == len(location_computers[location]):

            check_computer_send_mail(
                last_time=None,
                compare_time=LOCATION_OFFLINE_30MIN,
                computer=None,
                alert_type="all offline 30 min",
                alert_obj=alert_names["all_offline"],
                alerted_target=location,
            )
            logger.warning(
                "All computers from location {} offline 30 min alert.", location
            )

        # query now for green comps in current location and compare to red comps
        # then decide if to send green email (meaning that all computers returned online)
        updated_loc_green_comps: list[m.Computer] = m.Computer.query.filter_by(
            alert_status="green", location_name=location
        ).all()

        logger.error(
            "All green. location: {}. Red {}, Green {}",
            location,
            len(red_comps),
            len(updated_loc_green_comps),
        )

        if len(red_comps) == 0 and len(updated_loc_green_comps) == 0:
            continue

        if len(red_comps) == len(updated_loc_green_comps) and len(all_green_li) > 0:
            send_alert_email(
                location, all_green_li[0], "all_green", "All computers are back online"
            )
            logger.error("All green email sent for location {}", location)


def daily_summary():
    """
    CLI command for celery worker.
    Sends daily summary to every user respectfully to user's asociated_with.
    """

    # TODO remove if unused
    # image = open("app/static/favicon.ico", "rb")
    # imgb = str(base64.b64encode(image.read()))[2:-1]
    # image.close()

    computers: list[m.Computer] = m.Computer.query.all()
    users: list[m.User] = m.User.query.filter(
        m.User.asociated_with != "global-full", m.User.asociated_with != "global-view"
    ).all()
    companies: list[m.Company] = m.Company.query.all()
    locations: list[m.Location] = m.Location.query.all()

    companies_names = [company.name for company in companies]
    locations_names = {loc.name: loc.company_name for loc in locations}

    # build a tree {company: {location: [computer, computer], location: [computer]}, company:...}
    company_loc_comp = {
        company.name: {
            loc.name: [comp for comp in computers if comp.location_name == loc.name]
            for loc in locations
            if loc.company_name == company.name
        }
        for company in companies
    }

    # get rid of users without association
    users = [user for user in users if user.asociated_with]
    # TODO remove after global users behavior is set
    dev = m.User(
        username="dev",
        email=CFG.DEV_EMAIL,
        password="dev",
        asociated_with="global-full",
    )
    users.append(dev)

    # TODO what if we have multiple users in same company/location?
    email_user = {user.email: user for user in users}
    email_company_locs_comps = {user.email: dict() for user in users}

    # asociate appropriate company trees to users
    for user in users:
        if user.asociated_with in companies_names:
            email_company_locs_comps[user.email] = {
                user.asociated_with: company_loc_comp[user.asociated_with]
            }
        elif user.asociated_with in locations_names:
            user_company = locations_names[user.asociated_with]
            email_company_locs_comps[user.email] = {
                user_company: company_loc_comp[user_company]
            }
        elif (
            user.asociated_with.lower() == "global-full"
            or user.asociated_with.lower() == "global-view"
        ):
            email_company_locs_comps[user.email] = company_loc_comp

    # TODO discuss and organize behavior for global users
    # for user in users:
    #     if (
    #         user.asociated_with.lower() == "global-full"
    #         or user.asociated_with.lower() == "global-view"
    #     ):
    #         email_computers[user.email] = computers

    for recipient in email_company_locs_comps:
        # do nothing for recipients with no computers
        if len(email_company_locs_comps[recipient]) == 0:
            continue

        red_comp = 0
        yellow_comp = 0
        green_comp = 0
        company_tables = list()
        # build html company - locations - computers tree
        for company in email_company_locs_comps[recipient]:
            company_online_comps = 0
            company_offline_comps = 0
            computer_loc_str_tables = list()

            for location in email_company_locs_comps[recipient][company]:
                location_str = f"<tr> <td></td> <td>{location}</td> <td></td> <td></td> \
                    <td></td> <td></td> <td></td> </tr>"
                computer_loc_str_tables.append(location_str)

                # NOTE this is shorter way, BUT doesn't count colors
                # computer_tables = " ".join(
                #     [
                #         f'<tr style="background-color: #{get_status_color(comp.alert_status)};"> <td></td> \
                #           <td></td> <td>{comp.computer_name}</td> <td>{comp.last_time_online}</td> \
                #           <td>{comp.last_download_time}</td> <td>{comp.alert_status}</td> <td>{comp.type}</td> </tr>'
                #         for comp in email_company_locs_comps[recipient][company][
                #             location
                #         ]
                #     ]
                # )

                computer_tables = list()
                for computer in email_company_locs_comps[recipient][company][location]:
                    computer_tables.append(
                        f'<tr style="background-color: #{get_status_color(computer.alert_status)};"> <td></td> \
                        <td></td> <td>{computer.computer_name}</td> <td>{computer.last_time_online}</td> \
                        <td>{computer.last_download_time}</td> <td>{computer.alert_status}</td> \
                        <td>{computer.device_role.capitalize()}</td> </tr>'
                    )
                    if "red" in str(computer.alert_status):
                        company_offline_comps += 1
                        red_comp += 1
                    elif "yellow" in str(computer.alert_status):
                        company_offline_comps += 1
                        yellow_comp += 1
                    elif "green" in str(computer.alert_status):
                        company_online_comps += 1
                        green_comp += 1
                computer_loc_str_tables.append(" ".join(computer_tables))

            company_str = f"<tr> <td>{company}</td> <td>Online {company_online_comps}</td> \
                <td>Offline {company_offline_comps}</td> <td></td> <td></td> <td></td> <td></td> </tr>"
            company_tables.append(company_str)
            company_tables.extend(computer_loc_str_tables)

        table_str = " ".join(company_tables)
        styles = """
            table {
            font-family: arial, sans-serif;
            border-colapse: collapse;
            width: 100%;
            }

            td, th {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
            }

            tr:nth-child(even) {
            background-color: #dddddd;
            }

            .h1-header {
            text-align: center
            }

            hr {
            margin-left: 10%;
            margin-right: 10%;
            }
        """

        html_template = f"""
            <html>
                <head>
                    <style>
                        {styles}
                    </style>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
                </head>
                <body class="bg-light">
                    <div class="container">
                    <div class="card my-10">
                        <div class="card-body">
                        <h1 class="h3 mb-2 h1-header">{email_user[recipient].asociated_with} computers</h1>

                        <hr>

                        <div class="space-y-3">

                            <table class="table table-striped table-bordered table-hover model-list"
                            style="border-collapse: collapse;"
                            >
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

                            <table class="table table-striped table-bordered table-hover model-list"
                                style="border-collapse: collapse;">
                                <thead>
                                    <tr>
                                        <th>
                                            Company
                                        </th>
                                        <th>
                                            Location
                                        </th>
                                        <th>
                                            Computer
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
                            <a href="https://emarvault.com/">
                                <img src="https://emarvault.com/static/img/emar_icon_web.jpg" alt="eMARVault" width="128px" height="128px">
                            </a>
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
        logger.debug("Recipients {} email sent", recipient)


def get_status_color(alert_status):
    row_colors = {"green": "1cc88a", "yellow": "f6c23e", "red": "e74a3b"}
    for color in row_colors:
        if color in str(alert_status):
            return row_colors[color]
    # if alert_status is None - retrun empty string to keep defualt color
    return ""


def reset_alert_statuses():
    """
    Set alert_status to green to all computers
    """
    computers: list[m.Computer] = m.Computer.query.all()

    for comp in computers:
        comp.alert_status = "green"
        comp.update()

    logger.debug("All computers alert_status updated to green")


def check_for_red(location_computers: list[m.Computer], message: str = ""):
    """Check if all computers in current location are red to deside what to do
    with current computer alert_status.

    Args:
        location_computers (list[m.Computer]): list of sqla Computer objects
        message (str): message to log

    Returns:
        bool: True or False which should continue or end parent func
    """
    comps_stats = [
        comp.alert_status
        for comp in location_computers
        if "red" in str(comp.alert_status)
    ]

    if len(comps_stats) == len(location_computers):
        # logger.info(message)
        return True
    return False
