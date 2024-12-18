from pydantic import BaseModel


class RegistrationDataWithLid(BaseModel):
    computer_name: str
    identifier_key: str
    lid: int
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = True
    device_location: str


class RegistrationDataWithOutLid(BaseModel):
    computer_name: str
    identifier_key: str
    device_type: str = "DESKTOP"
    device_role: str = "PRIMARY"
    enable_logs: bool = True
    activate_device: bool = False
    device_location: str = "unknown"
