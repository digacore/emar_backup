from pydantic import BaseModel


class Paging(BaseModel):
    hasMore: bool
    page: int
    pageSize: int
