from typing import Optional
from pydantic import BaseModel

class PrinterInfoDict(BaseModel):
    PrinterStatus: int
    Name: str

class PrinterInfo(BaseModel):
    computer_name: Optional[str]
    identifier_key: str
    printer_info: PrinterInfoDict
