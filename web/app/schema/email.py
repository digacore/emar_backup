from typing import Optional
from pydantic import BaseModel


class EmailSchema(BaseModel):
    from_email: str
    to_addresses: str
    subject: str
    body: str
    html_body: Optional[str]
    reply_to_address: Optional[str]
