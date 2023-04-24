from app.models import Company, Location, Computer


def update_companies_locations_statistic():
    # NOTE Update number of Computers in Locations
    computers = Computer.query.all()
    locations = Location.query.all()

    if locations:
        computer_location = [loc.location_name for loc in computers]
        for location in locations:
            location.computers_per_location = computer_location.count(location.name)
            # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
            computers_online_per_location = [
                comp.alert_status for comp in computers if comp.location == location
            ]
            computers_online = computers_online_per_location.count("green")
            location.computers_online = computers_online
            location.computers_offline = (
                len(computers_online_per_location) - computers_online
            )
            location.update()

    # NOTE Update number of Locations and Computers in Companies
    companies = Company.query.all()

    if companies:
        computer_company = [co.company_name for co in computers]
        location_company = [loc.company_name for loc in locations]
        for company in companies:
            company.total_computers = computer_company.count(company.name)
            # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
            computers_online_per_company = [
                comp.alert_status for comp in computers if comp.company == company
            ]
            computers_online = computers_online_per_company.count("green")
            company.computers_online = computers_online
            company.computers_offline = (
                len(computers_online_per_company) - computers_online
            )
            company.locations_per_company = location_company.count(company.name)
            company.update()
