import os
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

INPUT_LOG_FILE_PATH = Path("C://eMARVault") / "emar_log.txt"
OUTPUT_LOG_FILE_PATH = Path(os.environ["AppData"]) / "Emar" / "application.txt"


class Elapsed(BaseModel):
    repr: str
    seconds: float


class Exception(BaseModel):
    pass


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


def main():
    with open(INPUT_LOG_FILE_PATH, "r") as i_f:
        with open(OUTPUT_LOG_FILE_PATH, "w") as o_f:
            for line in i_f:
                log_line = LogLine.model_validate_json(line)
                o_f.writelines(
                    [
                        f"{log_line.record.time.repr}:{log_line.record.module}:{log_line.record.level.name}:{log_line.record.message}",
                        "\n",
                    ]
                )
    pass


if __name__ == "__main__":
    main()
