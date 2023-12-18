from pydantic import BaseModel


class ActivityData(BaseModel):
    computer_name: str
    identifier_key: str
    last_time_online: str
