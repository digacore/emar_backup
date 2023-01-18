from app import db


class ModelMixin(object):

    def save(self):
        # Save this model to the database.
        db.session.add(self)
        db.session.commit()
        return self

    def update(self):
        # Update this model to the database.
        db.session.commit()
        return self


# Add your own utility classes and functions here.
