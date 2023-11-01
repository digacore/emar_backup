from datetime import datetime

from sqlalchemy.orm import relationship

from app import db
from app.models.utils import ModelMixin


class AlertEmail(db.Model, ModelMixin):
    """
    Model to store info about alert emails
    (primary computer down, critical alert) that were sent
    """

    __tablename__ = "alert_emails"

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    location = relationship("Location", back_populates="alert_emails", lazy="select")

    def __repr__(self):
        return f"<{self.id} alert email.\
            Created_at: {self.created_at}. Location: {self.location.name}>"
