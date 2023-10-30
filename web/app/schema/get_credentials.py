from pydantic import BaseModel


class GetCredentials(BaseModel):
    computer_name: str
    identifier_key: str
