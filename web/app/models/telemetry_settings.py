from app import db
from app.models.utils import ModelMixin



class TelemetrySettings(db.Model, ModelMixin):
    __tablename__ = "telemetry_settings"

    id = db.Column(db.Integer, primary_key=True)
    send_printer_info = db.Column(db.Boolean, default=True)
    # those for logs_enabled in computer table
    send_agent_logs = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "<TelemetrySettings %r>" % self.id
