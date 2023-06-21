from typing import Optional
from pydantic import BaseModel


class CompanySFTPData(BaseModel):
    company_id: Optional[int]
    location_id: Optional[int]
