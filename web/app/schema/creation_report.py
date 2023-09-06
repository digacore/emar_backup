from pydantic import BaseModel
from datetime import datetime


class PartialCreationReport(BaseModel):
    data: list[dict] | None = None
    company_id: int | None = None
    company_name: str | None = None
    created_at: datetime | None = None
    status: str | None = None
    status_changed_by: str | None = None
    status_changed_at: datetime | None = None


class CreationReportAPIPath(BaseModel):
    report_id: int
