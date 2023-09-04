import json
import enum
from datetime import datetime

from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSON

from app import db
from app.models.utils import ModelMixin


class CreationReportStatus(enum.Enum):
    WAITING = "WAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# TODO: create logic of not deleting the companies but just marking them as "deleted"
# Then make company_id field as foreign key
class PCCCreationReport(db.Model, ModelMixin):
    __tablename__ = "pcc_creation_reports"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(JSON)
    company_id = db.Column(db.Integer, nullable=True)
    company_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        server_default=db.func.now(),
        nullable=False,
    )
    status = db.Column(Enum(CreationReportStatus), nullable=False)
    status_changed_by = db.Column(db.String(255), nullable=True)
    status_changed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Creation report: {self.id}. Created_at: {self.created_at}>"

    @property
    def data_as_obj(self):
        return json.loads(self.data)
