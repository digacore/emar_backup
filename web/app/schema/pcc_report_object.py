from pydantic import BaseModel


class PCCReportObject(BaseModel):
    id: int | None = None
    type: str
    name: str
    action: str
    pcc_org_id: str | None = None
    pcc_fac_id: int | None = None
    use_pcc_backup: bool | None = None
