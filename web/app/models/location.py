from datetime import datetime

from sqlalchemy.orm import relationship

from flask_admin.contrib.sqla import ModelView

from app import db
from app.models.utils import ModelMixin


class Location(db.Model, ModelMixin):

    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    company = relationship("Company", passive_deletes=True)
    company_name = db.Column(db.String, db.ForeignKey("companies.name", ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name

class LocationView(ModelView):
    can_delete = True
    column_hide_backrefs = False
    column_list = ["id", "name", "company_name", "created_at"]
    column_searchable_list = ["company_name"]
