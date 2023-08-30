from pydantic import BaseModel
from typing import Optional


class PccCreatedObject(BaseModel):
    type: str
    id: int
    name: str
    action: str
    pcc_org_id: Optional[str]
    pcc_fac_id: Optional[int]
