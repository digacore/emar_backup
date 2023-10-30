from pydantic import BaseModel

from .pcc_response_paging import Paging


class Facility(BaseModel):
    active: bool
    facId: int
    facilityName: str
    orgName: str
    orgUuid: str
    timeZone: str
    timeZoneOffset: int


class FacilitiesListResponse(BaseModel):
    data: list[Facility]
    paging: Paging
