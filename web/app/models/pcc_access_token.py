from datetime import datetime, timedelta

from app import db
from app.models.utils import ModelMixin


class PCCAccessToken(db.Model, ModelMixin):
    __tablename__ = "pcc_access_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_in = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.now, server_default=db.func.now()
    )

    def __repr__(self):
        return f"<Token: {self.token}. Expires_at: {str(self.created_at + timedelta(seconds=self.expires_in))}>"
