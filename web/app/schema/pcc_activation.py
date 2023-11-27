from pydantic import BaseModel
from typing import Optional
from datetime import date

from .pcc_response_paging import Paging


class FacilityActivationData(BaseModel):
    activationDate: date
    facId: int


class OrgActivationData(BaseModel):
    orgUuid: str
    scope: int
    facilityInfo: Optional[list[FacilityActivationData]]


class ActivationsResponse(BaseModel):
    data: list[OrgActivationData]
    paging: Paging
