from datetime import datetime, timedelta, timezone

from app import db
from app.logger import logger
from app import models as m
from config import BaseConfig as CFG


def create_superuser():
    global_company = m.Company.query.filter_by(is_global=True).first()
    if not m.User.query.filter(m.User.username == CFG.SUPER_USER_NAME).first():
        user = m.User(
            username=CFG.SUPER_USER_NAME,
            email=CFG.SUPER_USER_MAIL,
            password=CFG.SUPER_USER_PASS,
            company_id=global_company.id,
            role=m.UserRole.ADMIN,
            activated=True,
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

        companies = ["Global", "Atlas", "Dro", "WRC"]
        locations = {"Maywood": "Atlas", "Ararat": "Atlas", "SpringField": "Dro"}

        for company in companies:
            if company == "Global":
                m.Company(name=company, is_global=True).save()
            else:
                m.Company(name=company).save()

        for location in locations:
            m.Location(name=location, company_name=locations[location]).save()

        users = {
            "view_user": {
                "username": "test_user_view",
                "email": "test_user_view@mail.com",
                "password": "test_user_view",
                "activated": True,
                "company_id": m.Company.query.filter_by(is_global=True).first().id,
                "role": m.UserRole.USER,
            },
            "company_user": {
                "username": "test_user_company",
                "email": "test_user_company@mail.com",
                "password": "test_user_company",
                "activated": True,
                "company_id": m.Company.query.filter_by(name="Atlas").first().id,
                "role": m.UserRole.ADMIN,
            },
            "location_user": {
                "username": "test_user_location",
                "email": "test_user_location@mail.com",
                "password": "test_user_location",
                "activated": True,
                "company_id": m.Company.query.filter_by(name="Atlas").first().id,
                "role": m.UserRole.ADMIN,
                "location": m.Location.query.filter_by(name="Maywood").first(),
            },
            "location_dro_user": {
                "username": "location_dro_user",
                "email": "location_dro_user@mail.com",
                "password": "test_user_location",
                "activated": True,
                "company_id": m.Company.query.filter_by(name="Dro").first().id,
                "role": m.UserRole.ADMIN,
                "location": m.Location.query.filter_by(name="SpringField").first(),
            },
        }

        computers = {
            "comp1_intime": {
                "computer_name": "comp1_intime",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                ),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True),
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
            },
            "comp2_late": {
                "computer_name": "comp2_late",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                )
                - timedelta(seconds=60 * 60 * 13),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True)
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
            },
            "comp3_test": {
                "computer_name": "comp3_test",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                ),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True),
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
                "msi_version": "1.0.9.110769",
            },
            "comp4_test": {
                "computer_name": "comp4_test",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                ),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True),
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
            },
            "comp5_test": {
                "computer_name": "comp5_test",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                ),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True),
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
            },
            "comp7_no_download_time": {
                "computer_name": "comp7_no_download_time",
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True),
                "company_name": "Dro",
                "location_name": "SpringField",
                "sftp_host": "comp7_sftp_host",
                "sftp_username": "comp7_sftp_username",
                "sftp_password": "comp7_sftp_password",
                "sftp_folder_path": "comp7_sftp_folder_path",
                "identifier_key": "comp7_identifier_key",
                "folder_password": "pass",
                "manager_host": "comp7_manager_host",
                "files_checksum": dict(),
            },
            "comp6_late": {
                "computer_name": "comp6_late",
                "last_download_time": CFG.offset_to_est(
                    datetime.now(timezone.utc), True
                )
                - timedelta(seconds=60 * 60 * 50),
                "last_time_online": CFG.offset_to_est(datetime.now(timezone.utc), True)
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
            },
        }

        for user in users:
            new_user = m.User(
                username=users[user]["username"],
                email=users[user]["email"],
                password=users[user]["password"],
                activated=users[user]["activated"],
                company_id=users[user]["company_id"],
                role=users[user]["role"],
            )

            if "location" in users[user]:
                new_user.location = [users[user]["location"]]

            new_user.save()

        for computer in computers:
            if "last_download_time" not in computers[computer]:
                m.Computer(
                    computer_name=computers[computer]["computer_name"],
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
                ).save()
            elif "msi_version" in computers[computer]:
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
        m.DesktopClient(
            mimetype="application/octet-stream",
            filename="new_test_version.msi",
            blob=b"new_test_bytes",
            size=345,
            name="new_test_version",
            version="1.0.9.110769",
            description="new version",
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
