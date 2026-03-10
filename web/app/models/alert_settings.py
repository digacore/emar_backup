from datetime import datetime

from app import db
from app.models.utils import ModelMixin


class AlertSettings(db.Model, ModelMixin):
    """
    Global alert configuration (single row).
    Support emails receive all offline alerts (critical, primary, alternate).
    Falls back to ALERT_SUPPORT_EMAILS env var when empty.
    """

    __tablename__ = "alert_settings"

    id = db.Column(db.Integer, primary_key=True)
    support_emails = db.Column(db.Text, nullable=True, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertSettings id={self.id}>"
