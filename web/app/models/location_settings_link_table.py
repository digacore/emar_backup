from app import db
from app.models.utils import ModelMixin



class LocationSettingsLinkTable(db.Model, ModelMixin):
    __tablename__ = "location_settings_link_table"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"))
    telemetry_settings_id = db.Column(db.Integer, db.ForeignKey("telemetry_settings.id"),default=1)

    def __repr__(self):
        return {
            "location_id": self.location_id,
            "telemetry_settings_id": self.telemetry_settings_id,
        }