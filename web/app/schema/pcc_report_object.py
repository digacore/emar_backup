from pydantic import BaseModel
from typing import Optional


class PCCReportObject(BaseModel):
    type: str
    name: str
    id: Optional[int]
    action: str
    pcc_org_id: Optional[str]
    pcc_fac_id: Optional[int]
