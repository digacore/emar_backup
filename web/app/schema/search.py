from pydantic import BaseModel


class SearchCompanyObj(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
