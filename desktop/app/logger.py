import os

# ruff: noqa: E402
os.environ["LOGURU_COLORIZE"] = "NO"
from loguru import logger
from pathlib import Path

from app.consts import STORAGE_PATH

LOG_FORMAT = "{time} - {name} - {level} - {message}"
logger.add(
    sink=(Path(STORAGE_PATH) / "emar_log.txt"),
    format=LOG_FORMAT,
    serialize=True,
    level="DEBUG",
    colorize=False,
)
