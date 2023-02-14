from datetime import datetime

from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.controllers import MyModelView


class User(db.Model, UserMixin, ModelMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    # TODO permission field. Global or company or location.
    asociated_with = db.Column(db.String(64), default="global") 

    last_time_online = db.Column(db.DateTime)

    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def authenticate(cls, user_id, password):
        user = cls.query.filter(
            db.or_(func.lower(cls.username) == func.lower(user_id), func.lower(cls.email) == func.lower(user_id))
        ).first()
        if user is not None and check_password_hash(user.password, password):
            return user

    def __repr__(self):
        return f"<User: {self.username}>"


class AnonymousUser(AnonymousUserMixin):
    pass


PERMISSIONS = [('Global-full', 'Global-full'), ('Global-view', 'Global-view'),]

# NOTE option 1: set hashed password through model (flask-admin field only)
class UserView(RowActionListMixin, MyModelView):

    column_list = [
        "id",
        "username",
        "email",
        "asociated_with",
        "activated",
        "last_time_online",
        "created_at"
    ]

    form_choices = {
        'asociated_with': PERMISSIONS
    }
    def on_model_change(self, form, model, is_created):
        model.password_hash = generate_password_hash(model.password_hash)
        # # as another example
        # if is_created:
        #     model.created_at = datetime.now()

    def _can_edit(self, model):
        # return True to allow edit
        print("current_user", current_user.username, current_user.asociated_with)
        if current_user.asociated_with == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        print("current_user", current_user.username, current_user.asociated_with)
        if current_user.asociated_with == "global-full":
            return True
        else:
            return False

    def allow_row_action(self, action, model):

        if isinstance(action, EditRowAction):
            return self._can_edit(model)

        if isinstance(action, DeleteRowAction):
            return self._can_delete(model)

        # otherwise whatever the inherited method returns
        return super().allow_row_action(action, model)


# NOTE option 2: set hashed password through sqlalchemy event (any password setter if affected)
# from sqlalchemy import event
# from werkzeug.security import generate_password_hash


# @event.listens_for(User.password, 'set', retval=True)
# def hash_user_password(target, value, oldvalue, initiator):
#     if value != oldvalue:
#         return generate_password_hash(value)
#     return value