from datetime import datetime, timedelta

from app import db
from app.logger import logger
from app import models as m
from config import BaseConfig as CFG


def create_superuser():
    if not m.User.query.filter(m.User.username == CFG.SUPER_USER_NAME).first():
        user = m.User(
            username=CFG.SUPER_USER_NAME,
            email=CFG.SUPER_USER_MAIL,
            password=CFG.SUPER_USER_PASS,
            asociated_with="global-full",
        )
        user.save()
        logger.info("Superuser created")
    else:
        logger.info("Superuser already exists")


def init_db(test_me: bool = False):
    """fill database with initial data
    Args:
        test_me (bool, optional): will add test data if set True. Defaults to False.
    """
    if test_me:
        logger.info("Generate test data")

        users = {
            "view_user": {
                "username": "test_user_view",
                "email": "test_user_view@mail.com",
                "password": "test_user_view",
                "asociated_with": "global-view",
            },
            "company_user": {
                "username": "test_user_company",
                "email": "test_user_company@mail.com",
                "password": "test_user_company",
                "asociated_with": "Atlas",
            },
            "location_user": {
                "username": "test_user_location",
                "email": "test_user_location@mail.com",
                "password": "test_user_location",
                "asociated_with": "Maywood",
            },
            "location_dro_user": {
                "username": "location_dro_user",
                "email": "location_dro_user@mail.com",
                "password": "test_user_location",
                "asociated_with": "SpringField",
            },
        }

        companies = ["Atlas", "Dro", "WRC"]
        locations = {"Maywood": "Atlas", "SpringField": "Dro"}

        computers = {
            "comp1_intime": {
                "computer_name": "comp1_intime",
                "last_download_time": CFG.offset_to_est(datetime.now(), True),
                "last_time_online": CFG.offset_to_est(datetime.now(), True),
                "company_name": "Atlas",
                "location_name": "Maywood",
                "sftp_host": "comp1_sftp_host",
                "sftp_username": "comp1_sftp_username",
                "sftp_password": "comp1_sftp_password",
                "sftp_folder_path": "comp1_sftp_folder_path",
                "identifier_key": "comp1_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp1_manager_host",
                "files_checksum": dict(),
                "msi_version": "stable",
                "alert_status": "green",
            },
            "comp2_late": {
                "computer_name": "comp2_late",
                "last_download_time": CFG.offset_to_est(datetime.now(), True)
                - timedelta(seconds=60 * 60 * 13),
                "last_time_online": CFG.offset_to_est(datetime.now(), True)
                - timedelta(seconds=60 * 60 * 13),
                "company_name": "Atlas",
                "location_name": "Maywood",
                "sftp_host": "comp2_sftp_host",
                "sftp_username": "comp2_sftp_username",
                "sftp_password": "comp2_sftp_password",
                "sftp_folder_path": "comp2_sftp_folder_path",
                "identifier_key": "comp2_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp2_manager_host",
                "files_checksum": dict(),
                "msi_version": "stable",
                "alert_status": "red",
            },
            "comp3_test": {
                "computer_name": "comp3_test",
                "last_download_time": CFG.offset_to_est(datetime.now(), True),
                "last_time_online": CFG.offset_to_est(datetime.now(), True),
                "company_name": "Atlas",
                "location_name": "Maywood",
                "sftp_host": "comp3_sftp_host",
                "sftp_username": "comp3_sftp_username",
                "sftp_password": "comp3_sftp_password",
                "sftp_folder_path": "comp3_sftp_folder_path",
                "identifier_key": "comp3_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp3_manager_host",
                "files_checksum": dict(),
                "msi_version": "stable",
                "alert_status": "yellow",
            },
            "comp4_test": {
                "computer_name": "comp4_test",
                "last_download_time": CFG.offset_to_est(datetime.now(), True),
                "last_time_online": CFG.offset_to_est(datetime.now(), True),
                "company_name": "Atlas",
                "location_name": "Maywood",
                "sftp_host": "comp4_sftp_host",
                "sftp_username": "comp4_sftp_username",
                "sftp_password": "comp4_sftp_password",
                "sftp_folder_path": "comp4_sftp_folder_path",
                "identifier_key": "comp4_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp4_manager_host",
                "files_checksum": dict(),
                "msi_version": "stable",
                "alert_status": "green",
            },
            "comp5_test": {
                "computer_name": "comp5_test",
                "last_download_time": CFG.offset_to_est(datetime.now(), True),
                "last_time_online": CFG.offset_to_est(datetime.now(), True),
                "company_name": "Atlas",
                "location_name": "Maywood",
                "sftp_host": "comp5_sftp_host",
                "sftp_username": "comp5_sftp_username",
                "sftp_password": "comp5_sftp_password",
                "sftp_folder_path": "comp5_sftp_folder_path",
                "identifier_key": "comp5_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp5_manager_host",
                "files_checksum": dict(),
                "alert_status": "green",
            },
            "comp6_late": {
                "computer_name": "comp6_test",
                "last_download_time": CFG.offset_to_est(datetime.now(), True)
                - timedelta(seconds=60 * 60 * 50),
                "last_time_online": CFG.offset_to_est(datetime.now(), True)
                - timedelta(seconds=60 * 60 * 50),
                "company_name": "Dro",
                "location_name": "SpringField",
                "sftp_host": "comp6_sftp_host",
                "sftp_username": "comp6_sftp_username",
                "sftp_password": "comp6_sftp_password",
                "sftp_folder_path": "comp6_sftp_folder_path",
                "identifier_key": "comp6_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp6_manager_host",
                "files_checksum": dict(),
                "alert_status": "green",
            },
        }

        alerts = {
            "no_download_12h": {
                "name": "no_download_12h",
                "from_email": "",
                "to_addresses": "",
                "subject": "computer 12 hours alert!",
                "body": "computer had not download files for more then 12 hours.",
                "alert_status": "red",
            },
            "offline_12h": {
                "name": "offline_12h",
                "from_email": "",
                "to_addresses": "",
                "subject": "computer 12 hours offline alert!",
                "body": "computer had been offline for more then 12 hours.",
                "alert_status": "red",
            },
            "all_offline": {
                "name": "all_offline",
                "from_email": "",
                "to_addresses": "",
                "subject": "All computers offline 30 min alert!",
                "body": "All computers are offline more then 30 minutes.",
                "alert_status": "red",
            },
            "no_files_2h": {
                "name": "no_files_2h",
                "from_email": "",
                "to_addresses": "",
                "subject": "No new files over 2 h alert!",
                "body": "No new files were downloaded by all computers for over 2 hours.",
                "alert_status": "red",
            },
        }

        for user in users:
            m.User(
                username=users[user]["username"],
                email=users[user]["email"],
                password=users[user]["password"],
                asociated_with=users[user]["asociated_with"],
            ).save()

        for company in companies:
            m.Company(name=company).save()

        for location in locations:
            m.Location(name=location, company_name=locations[location]).save()

        for computer in computers:
            if "msi_version" in computer:
                m.Computer(
                    computer_name=computers[computer]["computer_name"],
                    last_download_time=computers[computer]["last_download_time"],
                    last_time_online=computers[computer]["last_time_online"],
                    company_name=computers[computer]["company_name"],
                    location_name=computers[computer]["location_name"],
                    sftp_host=computers[computer]["sftp_host"],
                    sftp_username=computers[computer]["sftp_username"],
                    sftp_password=computers[computer]["sftp_password"],
                    sftp_folder_path=computers[computer]["sftp_folder_path"],
                    identifier_key=computers[computer]["identifier_key"],
                    folder_password=computers[computer]["folder_password"],
                    manager_host=computers[computer]["manager_host"],
                    files_checksum=computers[computer]["files_checksum"],
                    msi_version=computers[computer]["msi_version"],
                    alert_status=computers[computer]["alert_status"],
                ).save()

            else:
                m.Computer(
                    computer_name=computers[computer]["computer_name"],
                    last_download_time=computers[computer]["last_download_time"],
                    last_time_online=computers[computer]["last_time_online"],
                    company_name=computers[computer]["company_name"],
                    location_name=computers[computer]["location_name"],
                    sftp_host=computers[computer]["sftp_host"],
                    sftp_username=computers[computer]["sftp_username"],
                    sftp_password=computers[computer]["sftp_password"],
                    sftp_folder_path=computers[computer]["sftp_folder_path"],
                    identifier_key=computers[computer]["identifier_key"],
                    folder_password=computers[computer]["folder_password"],
                    manager_host=computers[computer]["manager_host"],
                    files_checksum=computers[computer]["files_checksum"],
                    alert_status=computers[computer]["alert_status"],
                ).save()

        for alert in alerts:
            m.Alert(
                name=alerts[alert]["name"],
                from_email=alerts[alert]["from_email"],
                to_addresses=alerts[alert]["to_addresses"],
                subject=alerts[alert]["subject"],
                body=alerts[alert]["body"],
                alert_status=alerts[alert]["alert_status"],
            ).save()

        m.ClientVersion(name="stable").save()

        m.DesktopClient(
            mimetype="application/octet-stream",
            filename="test_version.msi",
            blob=b"test_bytes",
            size=345,
            name="test_version",
            version="1.0.1.1",
            description="test description",
            flag_name="stable",
        ).save()

        db.session.commit()


def empty_to_stable():
    """
    Convert empty msi_version field to 'stable'
    """
    computers = m.Computer.query.filter_by(msi_version=None).all()

    for computer in computers:
        computer.msi_version = "stable"
        computer.update()
