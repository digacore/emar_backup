from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class GetCredentials(BaseModel):
    # client: str
    # location: str
    # sftp_username: Optional[str]
    # sftp_password: Optional[str]
    # sftp_folder_path: Optional[str]
    computer_name: str
    identifier_key: str
