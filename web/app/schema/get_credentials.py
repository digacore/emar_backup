from pydantic import BaseModel


class GetCredentials(BaseModel):
    computer_name: str
    identifier_key: str


class GetPccDownloadData(GetCredentials):
    pcc_fac_id: str
