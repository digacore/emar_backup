from flask import jsonify

from app.logger import logger
from app.models import Company, Location, Computer
from app.schema import ActiveCompaniesResponse, ActiveCompanyResponse, ActiveFacilityResponse
from app.views.blueprint import BlueprintApi

companies_blueprint = BlueprintApi("/companies", __name__)


@companies_blueprint.get("/active")
@logger.catch
def get_active_companies():
    """
    Get all active companies with their facilities and active endpoint counts.
    
    Returns:
        ActiveCompaniesResponse: Nested structure of companies, facilities, and endpoint counts
    """
    # Query active companies (excluding global and deleted)
    companies = Company.query.filter(
        Company.activated.is_(True),
        Company.is_deleted.is_(False),
        Company.is_global.is_(False),
    ).all()

    company_responses = []

    for company in companies:
        # Determine version: "free" if is_trial is True, else "pro"
        version = "free" if company.is_trial else "pro"

        # Query active locations for this company
        locations = Location.query.filter(
            Location.company_id == company.id,
            Location.activated.is_(True),
            Location.is_deleted.is_(False),
        ).all()

        facility_responses = []

        for location in locations:
            # Count active computers (endpoints) for this location
            active_endpoints = Computer.query.filter(
                Computer.location_id == location.id,
                Computer.activated.is_(True),
                Computer.is_deleted.is_(False),
            ).count()

            facility_response = ActiveFacilityResponse(
                name=location.name,
                version=version,  # Inherited from company
                active_endpoints=active_endpoints,
            )
            facility_responses.append(facility_response)

        company_response = ActiveCompanyResponse(
            name=company.name,
            version=version,
            facilities=facility_responses,
        )
        company_responses.append(company_response)

    response = ActiveCompaniesResponse(companies=company_responses)

    return jsonify(response.dict()), 200
