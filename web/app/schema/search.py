from pydantic import BaseModel


class SearchObj(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
