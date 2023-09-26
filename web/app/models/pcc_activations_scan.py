import enum
from datetime import datetime

from sqlalchemy import Enum

from app import db
from app.models.utils import ModelMixin


class ScanStatus(enum.Enum):
    IN_PROGRESS = "IN PROGRESS"
    SUCCEED = "SUCCEED"
    FAILED = "FAILED"


class PCCActivationsScan(db.Model, ModelMixin):
    __tablename__ = "pcc_activations_scans"

    id = db.Column(db.Integer, primary_key=True)

    error = db.Column(db.Text)
    status = db.Column(Enum(ScanStatus), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        server_default=db.func.now(),
        nullable=False,
    )
    finished_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Activations scan ID: {self.id}. Created_at: {self.created_at}>"
