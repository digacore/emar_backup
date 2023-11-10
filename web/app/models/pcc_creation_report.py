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


class PCCCreationReport(db.Model, ModelMixin):
    __tablename__ = "pcc_creation_reports"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    data = db.Column(JSON)

    # NOTE: despite the fact that we have company_id and existence of company_name break 3rd normal form
    # we need to have company_name here for the case when report has WAITING status
    # and company hasn't been created in DB yet
    company_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        server_default=db.func.now(),
        nullable=False,
    )
    status = db.Column(Enum(CreationReportStatus), nullable=False)
    status_changed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Creation report: {self.id}. Created_at: {self.created_at}>"

    @property
    def data_as_obj(self):
        return json.loads(self.data)
