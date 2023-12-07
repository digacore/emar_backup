from app import models as m


def get_companies_merged_locations(
    primary_company: m.Company, secondary_company: m.Company
) -> list[m.Location]:
    """Get merged locations from two companies

    Args:
        primary_company (m.Company): Primary company
        secondary_company (m.Company): Secondary company

    Returns:
        list[m.Location]: List of merged locations
    """
    primary_company_locations: list[m.Location] = primary_company.locations.copy()

    secondary_company_locations: list[m.Location] = secondary_company.locations.copy()

    merged_locations = primary_company_locations
    for location in secondary_company_locations:
        if location not in merged_locations:
            merged_locations.append(location)

    return merged_locations


def get_merged_computers_list(
    primary_object: m.Company | m.Location, secondary_object: m.Company | m.Location
) -> list[m.Computer]:
    """Get merged computers from two companies/locations

    Args:
        primary_object (m.Company | m.Location): Primary company / location
        secondary_object(m.Company | m.Location): Secondary company / location

    Returns:
        list[m.Computer]: List of merged computers
    """
    primary_object_computers: list[m.Computer] = primary_object.computers.copy()

    secondary_object_computers: list[m.Computer] = secondary_object.computers.copy()

    merged_computers = primary_object_computers
    for computer in secondary_object_computers:
        if computer not in merged_computers:
            merged_computers.append(computer)

    return merged_computers


def has_access_to_computer(user: m.User, computer: m.Computer) -> bool:
    """Checks if user has access to computer information

    Args:
        user (m.User): user instance
        computer (m.Computer): computer instance

    Returns:
        bool: True if user has access to computer information
    """
    match user.permission:
        case m.UserPermissionLevel.GLOBAL:
            return True
        case m.UserPermissionLevel.COMPANY:
            return computer.company_id == user.company_id
        case m.UserPermissionLevel.LOCATION_GROUP:
            return computer.location_id in [
                loc.id for loc in user.location_group[0].locations
            ]
        case m.UserPermissionLevel.LOCATION:
            return computer.location_id == user.location[0].id
        case _:
            return False


def has_access_to_location(user: m.User, location: m.Location):
    """Checks if user has access to location information

    Args:
        user (m.User): user instance
        location (m.Location): location object

    Returns:
        bool: True if user has access to location information
    """
    match user.permission:
        case m.UserPermissionLevel.GLOBAL:
            return True
        case m.UserPermissionLevel.COMPANY:
            return location.company_id == user.company_id
        case m.UserPermissionLevel.LOCATION_GROUP:
            return location.id in [loc.id for loc in user.location_group[0].locations]
        case m.UserPermissionLevel.LOCATION:
            return location.id == user.location[0].id
        case _:
            return False


def has_access_to_company(user: m.User, company: m.Company):
    """Checks if user has access to company information

    Args:
        user (m.User): user instance
        company (m.Company): company object

    Returns:
        bool: True if user has access to location information
    """
    match user.permission:
        case m.UserPermissionLevel.GLOBAL:
            return True
        case m.UserPermissionLevel.COMPANY:
            return company.id == user.company_id
        case m.UserPermissionLevel.LOCATION_GROUP:
            return company.id == user.location_group[0].company_id
        case m.UserPermissionLevel.LOCATION:
            return company.id == user.location[0].company_id
        case _:
            return False


def get_telemetry_settings_for_computer(computer: m.Computer) -> m.TelemetrySettings:
    """Get telemetry settings for computer"""
    linked_table = m.ComputerSettingsLinkTable.query.filter_by(computer_id=computer.id).first()
    if not linked_table:
        linked_table = m.LocationSettingsLinkTable.query.filter_by(location_id=computer.location_id).first()
        if not linked_table:
            linked_table = m.CompanySettingsLinkTable.query.filter_by(company_id=computer.company_id).first()
            if not linked_table:
                linked_table = m.TelemetrySettings.query.get(1)
                if not linked_table:
                    linked_table = m.TelemetrySettings()
                    linked_table.save()
                    return linked_table
                return linked_table
    telemetry_settings = m.TelemetrySettings.query.filter_by(id=linked_table.telemetry_settings_id).first()
    return telemetry_settings