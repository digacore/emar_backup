from datetime import datetime, timedelta

from app.logger import logger
from app.models import (
    Company,
    Computer,
    ComputerStatus,
    DeviceRole,
    Location,
    LocationStatus,
)
from config import BaseConfig as CFG


def update_companies_locations_statistic():
    logger.info("<-----Start Updating Companies and Locations statistics----->")

    current_east_time = CFG.offset_to_est(datetime.utcnow(), True)

    # NOTE Update number of Locations and Computers in Companies
    companies = Company.query.all()

    for company in companies:
        company.locations_per_company = len(company.locations)
        company.total_computers = company.total_computers_counter

        offline_company_computers = company.total_offline_computers
        online_company_computers = Computer.query.filter(
            Computer.company_id == company.id,
            Computer.status == ComputerStatus.ONLINE.value,
        ).count()

        company.computers_online = online_company_computers
        company.computers_offline = offline_company_computers

        company.update()

    # NOTE Update number of Computers in Locations and status of Locations
    locations = Location.query.all()

    for location in locations:
        location.computers_per_location = location.total_computers

        online_location_computers = Computer.query.filter(
            Computer.location_id == location.id,
            Computer.activated.is_(True),
            Computer.last_download_time.is_not(None),
            Computer.last_download_time
            >= current_east_time - timedelta(hours=1, minutes=30),
        ).count()
        online_primary_computers = Computer.query.filter(
            Computer.location_id == location.id,
            Computer.activated.is_(True),
            Computer.device_role == DeviceRole.PRIMARY.value,
            Computer.last_download_time.is_not(None),
            Computer.last_download_time
            >= current_east_time - timedelta(hours=1, minutes=30),
        ).count()

        offline_location_computers = location.total_computers_offline

        location.computers_online = online_location_computers
        location.computers_offline = offline_location_computers

        if not location.activated:
            location.status = None
        elif online_primary_computers:
            location.status = LocationStatus.ONLINE
        elif online_location_computers:
            location.status = LocationStatus.ONLINE_PRIMARY_OFFLINE
        else:
            location.status = LocationStatus.OFFLINE

        location.update()

    logger.info("<-----Finish Updating Companies and Locations statistics----->")
