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
    primary_company_locations: list[m.Location] = primary_company.locations

    secondary_company_locations: list[m.Location] = secondary_company.locations

    merged_locations = primary_company_locations
    for location in secondary_company_locations:
        if location not in merged_locations:
            merged_locations.append(location)

    return merged_locations


def get_companies_merged_computers(
    primary_company: m.Company, secondary_company: m.Company
) -> list[m.Computer]:
    """Get merged computers from two companies

    Args:
        primary_company (m.Company): Primary company
        secondary_company (m.Company): Secondary company

    Returns:
        list[m.Computer]: List of merged computers
    """
    primary_company_computers: list[m.Computer] = primary_company.computers

    secondary_company_computers: list[m.Computer] = secondary_company.computers

    merged_computers = primary_company_computers
    for computer in secondary_company_computers:
        if computer not in merged_computers:
            merged_computers.append(computer)

    return merged_computers
