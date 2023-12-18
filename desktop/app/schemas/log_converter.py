from pydantic import BaseModel
from datetime import datetime


class Elapsed(BaseModel):
    repr: str
    seconds: float


class Exception(BaseModel):
    type: str
    value: str
    traceback: bool


class Extra(BaseModel):
    pass


class File(BaseModel):
    name: str
    path: str


class Level(BaseModel):
    icon: str
    name: str
    no: int


class Process(BaseModel):
    id: int
    name: str


class Thread(BaseModel):
    id: int
    name: str


class Time(BaseModel):
    repr: datetime
    timestamp: float


class LogRecord(BaseModel):
    elapsed: Elapsed
    exception: Exception | None = None
    extra: Extra
    file: File
    function: str
    level: Level
    line: int
    message: str
    module: str
    name: str
    process: Process
    thread: Thread
    time: Time


class LogLine(BaseModel):
    text: str
    record: LogRecord
