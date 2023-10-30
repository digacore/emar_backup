from app import db
from app.models.utils import ModelMixin


class PCCDailyRequest(db.Model, ModelMixin):

    __tablename__ = "pcc_daily_requests"

    id = db.Column(db.Integer, primary_key=True)

    requests_count = db.Column(db.Integer, nullable=False)
    reset_time = db.Column(db.DateTime, nullable=False, unique=True)

    def __repr__(self):
        return f"<{self.id}: reset time {self.reset_time} - requests count {self.requests_count}]>"
