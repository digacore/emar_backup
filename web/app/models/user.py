from datetime import datetime

from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from flask_admin.contrib.sqla import ModelView

from app import db
from app.models.utils import ModelMixin
from app.controllers import MyModelView


class User(db.Model, UserMixin, ModelMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    # TODO permission field. Global or company or location.
    asociated_with = db.Column(db.String(128), default="Global") 

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


# class UserView(ModelView):
#     company_atr = list()
#     location_atr = list()

#     def __init__(self, company: list, location: list) -> None:
#         self.company = company
#         self.location = location
#         # super().__init__()

#     can_delete = True
#     column_hide_backrefs = False
#     column_searchable_list = ["company_name", "location_name"]

#     @staticmethod
#     def query_com_loc(self):
#         # companies = self.company.query.all()
#         # locations = self.location.query.all()
#         setattr(self, "company_atr", self.company)
#         setattr(self, "location_atr", self.location)

#     form_choices = {
#         'asociated_with': [
#             "Global"
#             ] + [
#             location.name for location in location_atr
#             ] + [
#             company.name for company in company_atr
#             ]
#     }

# NOTE option 1: set hashed password through model (flask-admin field only)
class UserView(MyModelView):

    column_list = [
        "id",
        "username",
        "email",
        "asociated_with",
        "activated",
        "last_time_online",
        "created_at"
    ]

    def on_model_change(self, form, model, is_created):
        model.password_hash = generate_password_hash(model.password_hash)
        # # as another example
        # if is_created:
        #     model.created_at = datetime.now()  


# NOTE option 2: set hashed password through sqlalchemy event (any password setter if affected)
# from sqlalchemy import event
# from werkzeug.security import generate_password_hash


# @event.listens_for(User.password, 'set', retval=True)
# def hash_user_password(target, value, oldvalue, initiator):
#     if value != oldvalue:
#         return generate_password_hash(value)
#     return value