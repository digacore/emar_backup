from datetime import datetime

from sqlalchemy.orm import relationship

from app import db
from app.models.utils import ModelMixin


class DownloadBackupCall(db.Model, ModelMixin):
    """Model to store info about PCC API download backup calls"""

    __tablename__ = "download_backup_calls"

    id = db.Column(db.Integer, primary_key=True)

    computer_id = db.Column(
        db.Integer, db.ForeignKey("computers.id", ondelete="CASCADE"), nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    computer = relationship(
        "Computer", back_populates="download_backup_calls", lazy="select"
    )

    def __repr__(self):
        return f"<{self.id} download backup PCC API call.\
            Created_at: {self.created_at}. Computer: {self.computer.computer_name}>"
