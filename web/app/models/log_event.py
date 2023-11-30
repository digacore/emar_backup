import enum
from datetime import datetime

from sqlalchemy import Enum

from app import db
from app.models.utils import ModelMixin


class LogType(enum.Enum):
    HEARTBEAT = "HEARTBEAT"
    BACKUP_DOWNLOAD = "BACKUP_DOWNLOAD"
    CLIENT_UPGRADE = "CLIENT_UPGRADE"
    CLIENT_ERROR = "CLIENT_ERROR"
    STATUS_GREEN = "STATUS_GREEN"
    STATUS_YELLOW = "STATUS_YELLOW"
    STATUS_RED = "STATUS_RED"
    SPECIAL_STATUS = "SPECIAL_STATUS"
    PRINTER_STATUS = "PRINTER_STATUS"


class LogEvent(db.Model, ModelMixin):
    __tablename__ = "log_events"

    id = db.Column(db.Integer, primary_key=True)

    computer_id = db.Column(db.Integer, db.ForeignKey("computers.id"))

    log_type = db.Column(Enum(LogType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.String(128), server_default="", default="")

    def __repr__(self):
        return f"<{self.id}:{self.log_type} at {self.created_at}>"
