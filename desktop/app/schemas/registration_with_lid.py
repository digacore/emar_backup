from pydantic import BaseModel


class RegistrationDataWithLid(BaseModel):
    computer_name: str
    identifier_key: str
    lid: int
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = True


class RegistrationDataWithOutLid(BaseModel):
    computer_name: str
    identifier_key: str
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = False
