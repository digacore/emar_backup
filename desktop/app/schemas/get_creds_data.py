from pydantic import BaseModel


class GetCredentialsData(BaseModel):
    computer_name: str
    identifier_key: str


class GetPccDownloadData(GetCredentialsData):
    pcc_fac_id: int
