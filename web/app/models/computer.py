from datetime import datetime

from sqlalchemy.orm import relationship

from flask_admin.contrib.sqla import ModelView

from app import db
from app.models.utils import ModelMixin


class Computer(db.Model, ModelMixin):

    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)
    computer_name = db.Column(db.String(64), unique=True, nullable=False)

    location = relationship("Location", passive_deletes=True)
    location_name = db.Column(db.String, db.ForeignKey("locations.name", ondelete="CASCADE"))

    type = db.Column(db.String(128))
    alert_status = db.Column(db.String(128))
    activated = db.Column(db.Boolean, default=False)  # TODO do we need this one? Could computer be deactivated?
    created_at = db.Column(db.DateTime, default=datetime.now)

    sftp_host = db.Column(db.String(128))
    sftp_username = db.Column(db.String(64))
    sftp_password = db.Column(db.String(128))
    sftp_folder_path = db.Column(db.String(256))

    folder_password = db.Column(db.String(128))
    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="new_computer", nullable=False)

    company = relationship("Company", passive_deletes=True)
    company_name = db.Column(db.String, db.ForeignKey("companies.name", ondelete="CASCADE"))

    manager_host = db.Column(db.String(256))


class ComputerView(ModelView):
    can_delete = True
    column_hide_backrefs = False
    column_list = [
        "id",
        "computer_name",
        "alert_status",
        "company_name",
        "location_name",
        "type",
        "sftp_host",
        "sftp_username",
        "sftp_folder_path",
        "download_status",
        "last_download_time",
        "last_time_online",
        "identifier_key",
        "manager_host",
        
        "activated",
        "created_at"
        ]
    column_searchable_list = ["company_name", "location_name"]
