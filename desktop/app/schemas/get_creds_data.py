from pydantic import BaseModel


class GetCredentialsData(BaseModel):
    computer_name: str
    identifier_key: str
