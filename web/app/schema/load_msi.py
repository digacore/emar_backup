from pydantic import BaseModel


class LoadMSI(BaseModel):
    name: str
    version: str
    flag: str
    identifier_key: str
