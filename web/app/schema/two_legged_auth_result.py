from pydantic import BaseModel


class TwoLeggedAuthResult(BaseModel):
    access_token: str
    expires_in: int
