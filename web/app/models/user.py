import enum
from datetime import datetime

from sqlalchemy import func, Enum
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
from .location_group import LocationGroup

from .system_log import SystemLogType


users_alerts = db.Table(
    "users_alerts",
    db.Column("users_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("alerts_id", db.Integer, db.ForeignKey("alerts.id")),
)

users_to_group = db.Table(
    "users_to_group",
    db.metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    ),
    db.Column(
        "location_group_id",
        db.Integer,
        db.ForeignKey("location_groups.id"),
        nullable=False,
    ),
)

users_to_location = db.Table(
    "users_to_location",
    db.metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    ),
    db.Column(
        "location_id",
        db.Integer,
        db.ForeignKey("locations.id"),
        nullable=False,
    ),
)


class UserPermissionLevel(enum.Enum):
    GLOBAL = "GLOBAL"
    COMPANY = "COMPANY"
    LOCATION_GROUP = "LOCATION_GROUP"
    LOCATION = "LOCATION"


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(db.Model, UserMixin, ModelMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
    )

    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    asociated_with = db.Column(db.String(64))
    last_time_online = db.Column(db.DateTime)

    role = db.Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.ADMIN.value,
    )

    alerts = relationship(
        "Alert",
        secondary=users_alerts,
        passive_deletes=True,
        backref="users",
        lazy="select",
    )

    company = relationship("Company", backref="users", lazy="select")
    location_group = relationship(
        "LocationGroup", secondary=users_to_group, backref="users"
    )
    location = relationship("Location", secondary=users_to_location, backref="users")

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

    @property
    def permission(self):
        """Return user permission level"""
        # User has global permission
        if self.company.is_global:
            return UserPermissionLevel.GLOBAL
        # User has company permission
        elif not self.location_group and not self.location:
            return UserPermissionLevel.COMPANY
        # User has location group permission
        elif self.location_group:
            return UserPermissionLevel.LOCATION_GROUP
        # User has location permission
        elif self.location:
            return UserPermissionLevel.LOCATION

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
        "role",
        "asociated_with",
        "activated",
        "last_time_online",
        "created_at",
    ]

    column_labels = {
        "password_hash": "Password",
    }

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
        if is_created:
            model.password_hash = generate_password_hash(model.password_hash)
        # as another example
        # if is_created:
        #     model.created_at = datetime.now()

    def _can_create(self, model):
        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            or current_user.permission == UserPermissionLevel.COMPANY
        ) and current_user.role == UserRole.ADMIN:
            return True
        else:
            return False

    def _can_edit(self, model):
        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            or current_user.permission == UserPermissionLevel.COMPANY
        ) and current_user.role == UserRole.ADMIN:
            return True
        else:
            return False

    def _can_delete(self, model):
        if (
            (
                current_user.permission == UserPermissionLevel.GLOBAL
                or current_user.permission == UserPermissionLevel.COMPANY
            )
            and current_user.role == UserRole.ADMIN
            and model.id != current_user.id
        ):
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
        delattr(form, "password_hash")
        return form

    def create_form(self, obj=None):
        form = super(UserView, self).create_form(obj)
        form.asociated_with.choices = asociated_with_query_factory()
        return form

    def get_query(self):
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            or current_user.permission == UserPermissionLevel.COMPANY
        ) and current_user.role == UserRole.ADMIN:
            if "delete" in self.action_disallowed_list:
                self.action_disallowed_list.remove("delete")
            self.can_create = True
        else:
            if "delete" not in self.action_disallowed_list:
                self.action_disallowed_list.append("delete")
            self.can_create = False

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                result_query = self.session.query(self.model).filter(
                    self.model.username != "emarsuperuser"
                )
            case UserPermissionLevel.COMPANY:
                result_query = self.session.query(self.model).filter(
                    self.model.company_id == current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                result_query = self.session.query(self.model).filter(
                    self.model.location_group.any(
                        LocationGroup.id.in_(
                            [group.id for group in current_user.location_group]
                        )
                    )
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.session.query(self.model).filter(
                    self.model.location.any(
                        Location.id.in_(
                            [location.id for location in current_user.location]
                        )
                    )
                )
            case _:
                result_query = self.session.query(self.model).filter(
                    self.model.id == -1
                )

        # do not allow to edit superuser
        return result_query

    def get_count_query(self):
        actual_query = self.get_query()
        return actual_query.with_entities(func.count())


# NOTE option 2: set hashed password through sqlalchemy event (any password setter if affected)
# from sqlalchemy import event
# from werkzeug.security import generate_password_hash


# @event.listens_for(User.password, 'set', retval=True)
# def hash_user_password(target, value, oldvalue, initiator):
#     if value != oldvalue:
#         return generate_password_hash(value)
#     return value
