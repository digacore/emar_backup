from sqlalchemy.orm import relationship

from app import db
from app.models.utils import (
    ModelMixin,
)


class AdditionalLocation(db.Model, ModelMixin):
    __tablename__ = "additional_locations"

    id = db.Column(db.Integer, primary_key=True)

    computer_id = db.Column(db.Integer, db.ForeignKey("computers.id"))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"))

    computer = relationship("Computer", backref="additional_locations")
    location = relationship("Location", backref="additional_locations")

    def __repr__(self):
        return f"<{self.computer_id}: {self.location_id}>"
