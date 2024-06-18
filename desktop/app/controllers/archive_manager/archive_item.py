import enum
from datetime import datetime

from pydantic import BaseModel


class ItemType(enum.Enum):
    FILE = 1
    FOLDER = 2


class ArchiveItem(BaseModel):
    name: str
    item_type: ItemType
    size: int
    packed_size: int
    modified: datetime
    created: datetime
    accessed: datetime
    attributes: str
    encrypted: str
    comment: str
    crc: str
    method: str
    host_os: str
    version: str

    def is_folder(self) -> bool:
        return self.item_type == ItemType.FOLDER
