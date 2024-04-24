from pydantic import BaseModel


class SetSpecialStatus(BaseModel):
    computer_name: str
    identifier_key: str
    special_status: str
