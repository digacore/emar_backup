from datetime import datetime

from app import db
from app.models.utils import ModelMixin


class Company(db.Model, ModelMixin):

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name
