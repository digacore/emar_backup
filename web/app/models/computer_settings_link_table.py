from app import db
from app.models.utils import ModelMixin



class ComputerSettingsLinkTable(db.Model, ModelMixin):
    __tablename__ = "computer_settings_link_table"

    id = db.Column(db.Integer, primary_key=True)
    computer_id = db.Column(db.Integer, db.ForeignKey("computer.id"))
    telemetry_settings_id = db.Column(db.Integer, db.ForeignKey("telemetry_settings.id"),default=1)

    def __repr__(self):
        return {
            "computer_id": self.computer_id,
            "telemetry_settings_id": self.telemetry_settings_id,
        }