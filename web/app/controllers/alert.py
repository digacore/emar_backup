from datetime import datetime, timedelta

from sqlalchemy import or_, and_
from sqlalchemy.orm import Query
from flask import render_template
from flask_mail import Message

from app import models as m, mail, schema as s
from app.logger import logger

from config import BaseConfig as CFG


def send_email(
    subject: str,
    recipients: list[str],
    html: str,
    sender: str = CFG.MAIL_DEFAULT_SENDER,
):
    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        html=html,
    )

    mail.send(msg)
    logger.info("Email with subject {} was successfully sent", subject)


def send_critical_alert():
    """
    CLI command for celery worker.
    Sends critical alerts to users when location is offline (all the computers in the location are offline).
    """
    current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

    logger.info(
        "<---Start sending critical alerts. Time: {}--->",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Select all the active locations (except connected to trial and deactivated companies)
    locations: list[m.Location] = (
        m.Location.query.join(m.Company)
        .filter(
            m.Location.activated.is_(True),
            m.Company.is_trial.is_(False),
            m.Company.activated.is_(True),
        )
        .all()
    )

    for location in locations:
        location_computers_query: Query = m.Computer.query.filter(
            m.Computer.location_id == location.id,
            m.Computer.activated.is_(True),
        )
        with_prev_backups_comps = (
            location_computers_query.filter(m.Computer.last_download_time.is_not(None))
            .order_by(m.Computer.last_download_time.desc())
            .all()
        )

        # Check that there are no computers connected to the location
        # Or it has at least one computer that downloaded backup in last 2 hours
        if not location_computers_query.all() or (
            with_prev_backups_comps
            and current_east_time - with_prev_backups_comps[0].last_download_time
            < timedelta(hours=2)
        ):
            continue

        # Alert only every 2 hours
        if (
            with_prev_backups_comps
            and (
                current_east_time - with_prev_backups_comps[0].last_download_time
            ).seconds
            // 3600
            % 2
            != 0
        ):
            continue

        # Select all the company active users
        connected_users: list[m.User] = []
        all_company_users: list[m.User] = m.User.query.filter(
            m.User.activated.is_(True),
            m.User.company_id == location.company_id,
        ).all()

        for user in all_company_users:
            # If user has company level permission
            if user.permission == m.UserPermissionLevel.COMPANY:
                # Send to company level user only if location is offline more than 4 hours
                if (
                    with_prev_backups_comps
                    and current_east_time
                    - with_prev_backups_comps[0].last_download_time
                    < timedelta(hours=4)
                ):
                    continue
                else:
                    connected_users.append(user)
            # If user has location group level permission
            elif (
                location.group
                and user.permission == m.UserPermissionLevel.LOCATION_GROUP
                and user.location_group[0].id == location.group[0].id
            ):
                connected_users.append(user)
            # If user has location level permission
            elif (
                user.permission == m.UserPermissionLevel.LOCATION
                and user.location[0].id == location.id
            ):
                connected_users.append(user)
            else:
                continue

        if not connected_users:
            continue

        recipients = [user.email for user in connected_users]

        primary_computers = (
            location_computers_query.filter(
                m.Computer.device_role == m.DeviceRole.PRIMARY
            )
            .order_by(m.Computer.computer_name)
            .all()
        )
        alternate_computers = (
            location_computers_query.filter(
                m.Computer.device_role == m.DeviceRole.ALTERNATE
            )
            .order_by(m.Computer.computer_name)
            .all()
        )
        last_backup_time = (
            with_prev_backups_comps[0].last_download_time
            if with_prev_backups_comps
            else None
        )

        alert_html = render_template(
            "email/critical-alert-email.html",
            location=location,
            primary_computers=primary_computers,
            alternate_computers=alternate_computers,
            last_backup_time=last_backup_time,
        )

        try:
            send_email(
                subject=f"ALERT! Location {location.name} is offline",
                sender=CFG.MAIL_DEFAULT_SENDER,
                recipients=recipients,
                html=alert_html,
            )

            # Create record about new alert event
            new_alert_event = m.AlertEvent(
                location_id=location.id, alert_type=m.AlertEventType.CRITICAL_ALERT
            )
            new_alert_event.save()

            logger.info("Critical alert email sent for location {}", location.name)
        except Exception as err:
            logger.error(
                "Critical alert email was not sent for location {}. Error: {}",
                location.name,
                err,
            )

    logger.info("<---Finish sending critical alerts--->")


def send_primary_computer_alert():
    """
    CLI command for celery worker.
    Sends alerts to users when primary computer goes down.
    """
    current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

    logger.info(
        "<---Start sending primary computer down alerts. Time: {}--->",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Get all the active primary computers which downloaded last backup more than 2 hour ago
    # and not more than 3 hours ago
    all_primary_computers: list[m.Computer] = m.Computer.query.filter(
        m.Computer.activated.is_(True),
        m.Computer.device_role == m.DeviceRole.PRIMARY,
        m.Computer.last_download_time.between(
            current_east_time - timedelta(hours=3),
            current_east_time - timedelta(hours=2),
        ),
    ).all()

    for computer in all_primary_computers:
        if not computer.location or not computer.company or computer.company.is_trial:
            continue

        # Get all the active users connected to the computer
        connected_users: list[m.User] = []
        all_company_users: list[m.User] = m.User.query.filter(
            m.User.activated.is_(True), m.User.company_id == computer.company_id
        ).all()

        for user in all_company_users:
            if user.permission == m.UserPermissionLevel.COMPANY:
                connected_users.append(user)
            elif (
                computer.location.group
                and user.permission == m.UserPermissionLevel.LOCATION_GROUP
                and user.location_group[0].id == computer.location.group[0].id
            ):
                connected_users.append(user)
            elif (
                user.permission == m.UserPermissionLevel.LOCATION
                and user.location[0].id == computer.location.id
            ):
                connected_users.append(user)
            else:
                continue

        if not connected_users:
            continue

        recipients = [user.email for user in connected_users]

        try:
            send_email(
                subject=f"ALERT! Primary computer {computer.computer_name} is down",
                sender=CFG.MAIL_DEFAULT_SENDER,
                recipients=recipients,
                html=render_template(
                    "email/primary-computer-alert-email.html",
                    location=computer.location,
                    computer=computer,
                ),
            )

            # Create record about new alert event
            new_alert_event = m.AlertEvent(
                location_id=computer.location.id,
                alert_type=m.AlertEventType.PRIMARY_COMPUTER_DOWN,
            )
            new_alert_event.save()

            logger.info(
                "Primary computer down alert email sent for computer {}",
                computer.computer_name,
            )
        except Exception as err:
            logger.error(
                "Primary computer down alert email was not sent for computer {}. Error: {}",
                computer.computer_name,
                err,
            )

    logger.info("<---Finish sending primary computer down alerts--->")


def company_users_by_permission(
    company: m.Company,
) -> (list[m.User], dict[str, m.User], dict[str, m.User]):
    """
    Returns company users divided by their permission level

    Args:
        company (m.Company): company object

    Returns:
        (list[m.User], list[m.User], list[m.User]):
            (company_level_users, location_group_level_users, location_level_users)
    """
    company_users: list[m.User] = company.users

    # Divide receivers respecting their permission level
    company_level_users: list[m.User] = []
    location_group_level_users: dict[str, m.User] = {}
    location_level_users: dict[str, m.User] = {}

    for user in company_users:
        if not user.activated:
            continue

        match user.permission:
            case m.UserPermissionLevel.COMPANY:
                company_level_users.append(user)
            case m.UserPermissionLevel.LOCATION_GROUP:
                if location_group_level_users.get(user.location_group[0].name):
                    location_group_level_users[user.location_group[0].name].append(user)
                else:
                    location_group_level_users[user.location_group[0].name] = [user]
            case m.UserPermissionLevel.LOCATION:
                if location_level_users.get(user.location[0].name):
                    location_level_users[user.location[0].name].append(user)
                else:
                    location_level_users[user.location[0].name] = [user]

    return (company_level_users, location_group_level_users, location_level_users)


def divide_computers_by_location(
    computers: list[m.Computer],
) -> dict[str, list[m.Computer]]:
    """
    Returns dictionary with locations as keys and list of computers as values

    Args:
        computers (list[m.Computer]): list of Computer objects
    Returns:
        dict[str, list[m.Computer]]: dictionary with locations as keys and list of computers as values
    """
    computers_by_location: dict[str, s.ComputersByLocation] = {}

    for computer in computers:
        if computer.location_id and computers_by_location.get(computer.location_name):
            computers_by_location_obj = computers_by_location[computer.location_name]
            computer_obj = s.ComputerInfo.from_orm(computer)
            computers_by_location_obj.computers.append(computer_obj)
            computers_by_location[computer.location_name] = computers_by_location_obj

        elif computer.location_id:
            computer_obj = s.ComputerInfo.from_orm(computer)
            location_obj = s.LocationInfo.from_orm(computer.location)
            computers_by_location_obj = s.ComputersByLocation(
                location=location_obj, computers=[computer_obj]
            )
            computers_by_location[computer.location_name] = computers_by_location_obj

        else:
            continue

    return computers_by_location


def send_company_daily_summary(
    company: m.Company,
    target_users: list[m.User],
    computers_by_location: dict[str, m.Computer],
):
    """
    Sends daily summary to company users with company level permission.

    Args:
        company (m.Company): company object
        target_users (list[m.User]): list of users
        computers_by_location (dict[str, m.Computer]): dictionary with locations as keys
            and list of computers as values
    """
    recipients: list[str] = [user.email for user in target_users]

    try:
        send_email(
            subject="eMAR Vault Daily Summary",
            sender=CFG.MAIL_DEFAULT_SENDER,
            recipients=recipients,
            html=render_template(
                "email/daily-summary-email.html",
                computers_by_location=computers_by_location,
            ),
        )
        logger.info("Daily summary email sent for company users of {}", company.name)
    except Exception as err:
        logger.error(
            "Daily summary email was not sent for company users of {}. Error: {}",
            company.name,
            err,
        )


def send_location_group_daily_summary(
    company: m.Company,
    location_group_level_users: dict[str, list[m.User]],
    computers_by_location: dict[str, m.Computer],
):
    """
    Sends daily summary to company users with location group level permission.

    Args:
        company (m.Company): company object
        location_group_level_users (dict[str, list[m.User]]): dictionary with location group names as keys
            and list of users as values
        computers_by_location (dict[str, m.Computer]): dictionary with locations as keys
            and list of computers as values
    """
    for location_group, users in location_group_level_users.items():
        recipients: list[str] = [user.email for user in users]

        location_group: m.LocationGroup = m.LocationGroup.query.filter(
            m.LocationGroup.company_id == company.id,
            m.LocationGroup.name == location_group,
        ).first()
        location_names: list[str] = [
            location.name for location in location_group.locations
        ]

        # Filter computers by locations
        group_computers: dict[str, m.Computer] = {}
        for location in location_names:
            if computers_by_location.get(location):
                group_computers[location] = computers_by_location[location]

        if not users or not group_computers:
            continue

        try:
            send_email(
                subject="eMAR Vault Daily Summary",
                sender=CFG.MAIL_DEFAULT_SENDER,
                recipients=recipients,
                html=render_template(
                    "email/daily-summary-email.html",
                    computers_by_location=group_computers,
                ),
            )
            logger.info(
                "Daily summary email sent for location group users of {}",
                location_group,
            )
        except Exception as err:
            logger.error(
                "Daily summary email was not sent for location group users of {}. Error: {}",
                location_group,
                err,
            )


def send_location_daily_summary(
    location_level_users: dict[str, list[m.User]],
    computers_by_location: dict[str, m.Computer],
):
    """
    Sends daily summary to company users with location level permission.

    Args:
        location_level_users (dict[str, list[m.User]]): dictionary with location names as keys
            and list of users as values
        computers_by_location (dict[str, m.Computer]): dictionary with locations as keys
            and list of computers as values
    """
    for location, users in location_level_users.items():
        recipients: list[str] = [user.email for user in users]

        if not users or not computers_by_location.get(location):
            continue

        try:
            send_email(
                subject="eMAR Vault Daily Summary",
                sender=CFG.MAIL_DEFAULT_SENDER,
                recipients=recipients,
                html=render_template(
                    "email/daily-summary-email.html",
                    computers_by_location={location: computers_by_location[location]},
                ),
            )
            logger.info("Daily summary email sent for location users of {}", location)
        except Exception as err:
            logger.error(
                "Daily summary email was not sent for location users of {}. Error: {}",
                location,
                err,
            )


def send_daily_summary():
    """
    CLI command for celery worker.
    Sends daily summary about offline computers to users.
    """

    logger.info(
        "<---Start sending daily summary. Time: {}--->",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Select all the companies except global, trial and deactivated
    companies: list[m.Company] = m.Company.query.filter(
        m.Company.is_global.is_(False),
        m.Company.is_trial.is_(False),
        m.Company.activated.is_(True),
    ).all()

    for company in companies:
        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        offline_company_computers_query: Query = m.Computer.query.filter(
            and_(
                m.Computer.company_id == company.id,
                m.Computer.activated.is_(True),
                or_(
                    m.Computer.last_download_time.is_(None),
                    m.Computer.last_download_time
                    < current_east_time - timedelta(hours=1),
                ),
            )
        ).order_by(
            m.Computer.location_name,
            m.Computer.device_role.desc(),
            m.Computer.computer_name,
        )

        # If there are no users connected to the company or offline computers - skip it
        if not company.users or not offline_company_computers_query.all():
            continue

        (
            company_level_users,
            location_group_level_users,
            location_level_users,
        ) = company_users_by_permission(company)

        # TODO: divide with usage of locations (smaller loop)
        # Create dictionary with locations as keys and list of computers as values
        computers_by_location: dict[
            str, s.ComputersByLocation
        ] = divide_computers_by_location(offline_company_computers_query.all())

        # Send company level summary
        if company_level_users:
            send_company_daily_summary(
                company=company,
                target_users=company_level_users,
                computers_by_location=computers_by_location,
            )

        # Send location group level summary
        if location_group_level_users:
            send_location_group_daily_summary(
                company=company,
                location_group_level_users=location_group_level_users,
                computers_by_location=computers_by_location,
            )

        # Send location level summary
        if location_level_users:
            send_location_daily_summary(
                location_level_users=location_level_users,
                computers_by_location=computers_by_location,
            )

    logger.info("<---Finish sending daily summaries--->")


def send_weekly_summary():
    """
    CLI command for celery worker.
    Sends weekly summary about computers to users.
    """

    logger.info(
        "<---Start sending weekly summaries. Time: {}--->",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # Select all the companies except global and deactivated
    companies: list[m.Company] = m.Company.query.filter(
        m.Company.is_global.is_(False),
        m.Company.activated.is_(True),
    ).all()

    for company in companies:
        company_computers_query: Query = m.Computer.query.filter(
            m.Computer.company_id == company.id,
            m.Computer.activated.is_(True),
        ).order_by(
            m.Computer.location_name,
            m.Computer.device_role,
            m.Computer.computer_name,
        )

        # If there are no users connected to the company or computers - skip it
        if not company.users or not company_computers_query.all():
            continue

        (
            company_level_users,
            location_group_level_users,
            location_level_users,
        ) = company_users_by_permission(company)

        # Create dictionary with locations as keys and list of computers as values
        company_computers_by_location: dict[
            str, s.ComputersByLocation
        ] = divide_computers_by_location(company_computers_query.all())

        # Send company level summary
        if company_level_users:
            recipients: list[str] = [user.email for user in company_level_users]

            try:
                send_email(
                    subject="eMAR Vault Weekly Summary",
                    sender=CFG.MAIL_DEFAULT_SENDER,
                    recipients=recipients,
                    html=render_template(
                        "email/weekly-summary-email.html",
                        total_computers=company.total_computers_counter,
                        primary_computers_offline=company.primary_computers_offline,
                        total_offline_computers=company.total_offline_computers,
                        total_offline_locations=company.total_offline_locations,
                        computers_by_location=company_computers_by_location,
                        is_company_trial=company.is_trial,
                    ),
                )
                logger.info(
                    "Weekly summary email sent for company users of {}", company.name
                )
            except Exception as err:
                logger.error(
                    "Weekly summary email was not sent for company users of {}. Error: {}",
                    company.name,
                    err,
                )

        # Send location group level summary
        if location_group_level_users:
            for location_group_name, users in location_group_level_users.items():
                recipients: list[str] = [user.email for user in users]

                location_group: m.LocationGroup = m.LocationGroup.query.filter(
                    m.LocationGroup.company_id == company.id,
                    m.LocationGroup.name == location_group_name,
                ).first()

                location_ids: list[int] = [
                    location.id for location in location_group.locations
                ]

                group_computers_query = m.Computer.query.filter(
                    m.Computer.location_id.in_(location_ids),
                    m.Computer.activated.is_(True),
                ).order_by(
                    m.Computer.location_name,
                    m.Computer.device_role,
                    m.Computer.computer_name,
                )

                if not users or not group_computers_query.all():
                    continue

                # Create dictionary with locations as keys and list of computers as values
                group_computers_by_location: dict[
                    str, s.ComputersByLocation
                ] = divide_computers_by_location(group_computers_query.all())

                try:
                    send_email(
                        subject="eMAR Vault Weekly Summary",
                        sender=CFG.MAIL_DEFAULT_SENDER,
                        recipients=recipients,
                        html=render_template(
                            "email/weekly-summary-email.html",
                            total_computers=location_group.total_computers,
                            primary_computers_offline=location_group.primary_computers_offline,
                            total_offline_computers=location_group.total_offline_computers,
                            total_offline_locations=location_group.total_offline_locations,
                            computers_by_location=group_computers_by_location,
                            is_company_trial=company.is_trial,
                        ),
                    )
                    logger.info(
                        "Weekly summary email sent for location group users of {}",
                        location_group,
                    )
                except Exception as err:
                    logger.error(
                        "Weekly summary email was not sent for location group users of {}. Error: {}",
                        location_group,
                        err,
                    )

        # Send location level summary
        if location_level_users:
            for location_name, users in location_level_users.items():
                recipients: list[str] = [user.email for user in users]

                location: m.Location = m.Location.query.filter(
                    m.Location.company_id == company.id,
                    m.Location.name == location_name,
                ).first()

                activated_computers_query = m.Computer.query.filter(
                    m.Computer.location_id == location.id,
                    m.Computer.activated.is_(True),
                )

                online_computers = activated_computers_query.filter(
                    m.Computer.last_download_time.is_not(None),
                    m.Computer.last_download_time
                    >= CFG.offset_to_est(datetime.utcnow(), True) - timedelta(hours=1),
                ).count()

                # Check that location has activated computers and users otherwise skip it
                if not users or not activated_computers_query.all():
                    continue

                try:
                    send_email(
                        subject="eMAR Vault Weekly Summary",
                        sender=CFG.MAIL_DEFAULT_SENDER,
                        recipients=recipients,
                        html=render_template(
                            "email/weekly-summary-email.html",
                            total_computers=location.total_computers,
                            primary_computers_offline=location.primary_computers_offline,
                            total_offline_computers=location.total_computers_offline,
                            total_offline_locations=(0 if online_computers else 1),
                            computers_by_location={
                                location_name: company_computers_by_location[
                                    location_name
                                ]
                            },
                            is_company_trial=company.is_trial,
                        ),
                    )
                    logger.info(
                        "Weekly summary email sent for location users of {}",
                        location_name,
                    )
                except Exception as err:
                    logger.error(
                        "Weekly summary email was not sent for location users of {}. Error: {}",
                        location_name,
                        err,
                    )

    logger.info("<---Finish sending weekly summaries--->")
