import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.orm import relationship

from app import db
from app.models.utils import ModelMixin
from config import BaseConfig as CFG


class BackupLogType(enum.Enum):
    WITH_DOWNLOADS_PERIOD = "WITH_DOWNLOADS_PERIOD"
    NO_DOWNLOADS_PERIOD = "NO_DOWNLOADS_PERIOD"


class BackupLog(db.Model, ModelMixin):
    __tablename__ = "backup_logs"

    id = db.Column(db.Integer, primary_key=True)

    computer_id = db.Column(db.Integer, db.ForeignKey("computers.id"))

    backup_log_type = db.Column(Enum(BackupLogType), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    error = db.Column(db.String(128), server_default="", default="")
    notes = db.Column(db.String(128), server_default="", default="")

    computer = relationship(
        "Computer",
        back_populates="backup_logs",
        lazy="select",
    )

    def __repr__(self):
        return f"<{self.id}:{self.backup_log_type} from {self.start_time} to {self.end_time}>"

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def duration_as_str(self):
        duration_period = self.end_time - self.start_time
        return f"{duration_period.days} days \
            {duration_period.seconds // 3600} \
            hours {(duration_period.seconds // 60) % 60} minutes"

    @property
    def est_start_time(self):
        return CFG.offset_to_est(self.start_time, True)

    @property
    def est_end_time(self):
        return CFG.offset_to_est(self.end_time, True)
