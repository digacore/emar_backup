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


class RowActionListMixin(object):

    list_template = 'admin/list.html'

    def allow_row_action(self, action, model):
        return True
