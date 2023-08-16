from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import current_user, UserMixin, AnonymousUserMixin
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin

from app.utils import MyModelView

from .company import Company
from .location import Location

from .system_log import SystemLogType


users_alerts = db.Table(
    "users_alerts",
    db.Column("users_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("alerts_id", db.Integer, db.ForeignKey("alerts.id")),
)


class User(db.Model, UserMixin, ModelMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    asociated_with = db.Column(db.String(64))

    alerts = relationship(
        "Alert",
        secondary=users_alerts,
        passive_deletes=True,
        backref="users",
        lazy="select",
    )

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
            db.or_(
                func.lower(cls.username) == func.lower(user_id),
                func.lower(cls.email) == func.lower(user_id),
            )
        ).first()
        if user is not None and check_password_hash(user.password, password):
            return user

    def __repr__(self):
        return f"<User: {self.username}>"


def asociated_with_query_factory():
    USER_PERMISSIONS = [
        ("Global-full", "Global-full"),
        ("Global-view", "Global-view"),
    ]

    # NOTE this try block is used to avoid appending during app launch
    try:
        locations = db.session.query(Location).all()
        companies = db.session.query(Company).all()

        for location in locations:
            USER_PERMISSIONS.append((location, f"Location-{location}"))

        for company in companies:
            USER_PERMISSIONS.append((company, f"Company-{company}"))
    except RuntimeError:
        # NOTE avoid situation when app starts and asociated_with_query_factory() is called in UserView
        pass

    return USER_PERMISSIONS


class AnonymousUser(AnonymousUserMixin):
    pass


# NOTE option 1: set hashed password through model (flask-admin field only)
class UserView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "UserView"

    column_list = [
        "id",
        "username",
        "email",
        "asociated_with",
        "activated",
        "last_time_online",
        "created_at",
    ]

    column_searchable_list = column_list
    column_filters = column_list

    form_choices = {"asociated_with": asociated_with_query_factory()}

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    action_disallowed_list = ["delete"]

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that user was created or updated
        if is_created:
            create_system_log(SystemLogType.USER_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.USER_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that user was deleted
        create_system_log(SystemLogType.USER_DELETED, model, current_user)

    def on_model_change(self, form, model, is_created):
        model.password_hash = generate_password_hash(model.password_hash)
        # as another example
        # if is_created:
        #     model.created_at = datetime.now()

    def _can_create(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_edit(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        if str(current_user.asociated_with).lower() == "global-full":
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

    def edit_form(self, obj):
        form = super(UserView, self).edit_form(obj)
        form.asociated_with.choices = asociated_with_query_factory()
        return form

    def create_form(self, obj=None):
        form = super(UserView, self).create_form(obj)
        form.asociated_with.choices = asociated_with_query_factory()
        return form

    def get_query(self):

        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
                result_query = self.session.query(self.model).filter(
                    self.model.username != "emarsuperuser"
                )
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False
                result_query = self.session.query(self.model).filter(
                    self.model.username == "None"
                )

        # do not allow to edit superuser
        return result_query


# NOTE option 2: set hashed password through sqlalchemy event (any password setter if affected)
# from sqlalchemy import event
# from werkzeug.security import generate_password_hash


# @event.listens_for(User.password, 'set', retval=True)
# def hash_user_password(target, value, oldvalue, initiator):
#     if value != oldvalue:
#         return generate_password_hash(value)
#     return value
