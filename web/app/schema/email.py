from typing import Optional
from pydantic import BaseModel


class EmailSchema(BaseModel):
    from_email: Optional[str]
    to_addresses: list
    subject: str
    body: str
    html_body: Optional[str]
    alerted_target: str
    alert_status: str
