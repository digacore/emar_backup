import json
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from app import db
from app.models.utils import ModelMixin


# TODO: create logic of not deleting the companies but just marking them as "deleted"
# Then make company_id field as foreign key
class PCCCreationReport(db.Model, ModelMixin):
    __tablename__ = "pcc_creation_reports"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(JSON)
    company_id = db.Column(db.Integer, nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        server_default=db.func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Creation report: {self.id}. Created_at: {self.created_at}>"

    @property
    def data_as_obj(self):
        return json.loads(self.data)
