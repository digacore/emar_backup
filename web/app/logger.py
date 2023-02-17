from pathlib import Path
from loguru import logger


log_format = "{time} - {name} - {level} - {message}"
home_log = Path.home() / "emar_server_logs.txt"

logger.add(
    Path.home(),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True,
    rotation="1000 MB",
    compression="zip"
)
