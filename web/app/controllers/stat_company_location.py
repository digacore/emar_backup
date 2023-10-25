from app.models import Company, Location, Computer, ComputerStatus
from app.logger import logger


def update_companies_locations_statistic():
    logger.info("<-----Start Updating Companies and Locations statistics----->")

    # NOTE Update number of Locations and Computers in Companies
    companies = Company.query.all()

    for company in companies:
        company.locations_per_company = len(company.locations)
        company.total_computers = len(company.computers)

        offline_company_computers = company.total_offline_computers
        online_company_computers = Computer.query.filter(
            Computer.company_id == company.id,
            Computer.status == ComputerStatus.ONLINE.value,
        ).count()

        company.computers_online = online_company_computers
        company.computers_offline = offline_company_computers

        company.update()

    # NOTE Update number of Computers in Locations
    locations = Location.query.all()

    for location in locations:
        location.computers_per_location = len(location.computers)

        online_location_computers = Computer.query.filter(
            Computer.location_id == location.id,
            Computer.status == ComputerStatus.ONLINE.value,
        ).count()
        offline_location_computers = location.total_computers_offline

        location.computers_online = online_location_computers
        location.computers_offline = offline_location_computers

        location.update()

    logger.info("<-----Finish Updating Companies and Locations statistics----->")
