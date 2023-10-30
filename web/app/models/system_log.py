import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.orm import relationship

from app import db
from app.models.utils import ModelMixin


class SystemLogType(enum.Enum):
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"

    COMPUTER_CREATED = "COMPUTER_CREATED"
    COMPUTER_UPDATED = "COMPUTER_UPDATED"
    COMPUTER_DELETED = "COMPUTER_DELETED"

    COMPANY_CREATED = "COMPANY_CREATED"
    COMPANY_UPDATED = "COMPANY_UPDATED"
    COMPANY_DELETED = "COMPANY_DELETED"

    LOCATION_CREATED = "LOCATION_CREATED"
    LOCATION_UPDATED = "LOCATION_UPDATED"
    LOCATION_DELETED = "LOCATION_DELETED"


class SystemLog(db.Model, ModelMixin):

    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    log_type = db.Column(Enum(SystemLogType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    object_id = db.Column(db.Integer, nullable=False)
    object_name = db.Column(db.String(128), nullable=False)
    object_url = db.Column(db.String(256), nullable=False)

    created_by = relationship("User", passive_deletes=False, lazy="select")

    def __repr__(self):
        return f"<{self.id}:{self.log_type} at {self.created_at}>"
