from pydantic import BaseModel


class CompanySFTPData(BaseModel):
    company_id: int
