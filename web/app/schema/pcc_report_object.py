from enum import Enum
from pydantic import BaseModel


class PCCReportType(str, Enum):
    COMPANY = "COMPANY"
    LOCATION = "LOCATION"


class PCCReportAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"


class PCCReportObject(BaseModel):
    id: int | None = None
    type: PCCReportType
    name: str
    action: PCCReportAction
    pcc_org_id: str | None = None
    pcc_fac_id: int | None = None
    use_pcc_backup: bool | None = None
