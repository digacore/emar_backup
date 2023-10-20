from pydantic import BaseModel

from .computer import ComputerInfo
from .location import LocationInfo


class ComputersByLocation(BaseModel):
    location: LocationInfo
    computers: list[ComputerInfo]
