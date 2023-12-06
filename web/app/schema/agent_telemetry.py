from pydantic import BaseModel

from .printer_info import PrinterInfo

class AgentTelemetry(BaseModel):
    computer_name: str
    machine_id: str | None = None
    identifier_key: str | None = None
    printer_info: PrinterInfo | None = None

class TelemetryRequestId(BaseModel):
    identifier_key: str