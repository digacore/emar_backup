from app import db
from app.models.utils import ModelMixin



class CompanySettingsLinkTable(db.Model, ModelMixin):
    __tablename__ = "company_settings_link_table"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    telemetry_settings_id = db.Column(db.Integer, db.ForeignKey("telemetry_settings.id"),default=1)

    def __repr__(self):
        return {
            "company_id": self.company_id,
            "telemetry_settings_id": self.telemetry_settings_id,
        }
