from pydantic import BaseModel
from typing import List


class ActiveFacilityResponse(BaseModel):
    """Response model for an active facility (location)"""
    name: str
    version: str  # "free" or "pro"
    active_endpoints: int


class ActiveCompanyResponse(BaseModel):
    """Response model for an active company with its facilities"""
    name: str
    version: str  # "free" or "pro"
    facilities: List[ActiveFacilityResponse]


class ActiveCompaniesResponse(BaseModel):
    """Root response model containing all active companies"""
    companies: List[ActiveCompanyResponse]
