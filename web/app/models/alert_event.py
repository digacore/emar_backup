import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.orm import relationship

from app import db
from app.models.utils import ModelMixin


class AlertEventType(enum.Enum):
    PRIMARY_COMPUTER_DOWN = "PRIMARY_COMPUTER_DOWN"
    CRITICAL_ALERT = "CRITICAL_ALERT"


class AlertEvent(db.Model, ModelMixin):
    """
    Model to store info about alert events
    (primary computer down, critical alert) for each location
    """

    __tablename__ = "alert_events"

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)

    alert_type = db.Column(Enum(AlertEventType), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    location = relationship("Location", back_populates="alert_events", lazy="select")

    def __repr__(self):
        return f"<{self.id} alert event.\
            Created_at: {self.created_at}. Location: {self.location.name}>"
