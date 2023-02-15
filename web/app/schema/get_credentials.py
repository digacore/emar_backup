from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class GetCredentials(BaseModel):
    computer_name: str
    identifier_key: str
