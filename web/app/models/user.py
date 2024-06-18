import enum
from datetime import datetime

from flask import flash
from flask_admin.babel import gettext
from flask_admin.contrib.sqla import tools
from flask_admin.model.template import DeleteRowAction, EditRowAction
from flask_login import AnonymousUserMixin, UserMixin, current_user
from sqlalchemy import Enum, and_, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.logger import logger
from app.models.utils import (
    ActivatedMixin,
    ModelMixin,
    QueryWithSoftDelete,
    RowActionListMixin,
    SoftDeleteMixin,
)
from app.utils import MyModelView
from config import BaseConfig as CFG

from .company import Company
from .location import Location
from .location_group import LocationGroup
from .system_log import SystemLogType

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
    ANONYMOUS = "ANONYMOUS"


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(db.Model, UserMixin, ModelMixin, SoftDeleteMixin, ActivatedMixin):
    __tablename__ = "users"

    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=CFG.GLOBAL_COMPANY_ID,
    )

    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_time_online = db.Column(db.DateTime)

    role = db.Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.ADMIN.value,
    )

    company = relationship("Company", back_populates="users", lazy="select")

    location_group = relationship(
        "LocationGroup",
        secondary=users_to_group,
        backref="users",
        secondaryjoin=and_(
            users_to_group.c.location_group_id == LocationGroup.id,
            LocationGroup.is_deleted.is_(False),
        ),
    )

    location = relationship(
        "Location",
        secondary=users_to_location,
        backref="users",
        secondaryjoin=and_(
            users_to_location.c.location_id == Location.id,
            Location.is_deleted.is_(False),
        ),
    )

    def delete(self, commit: bool = True):
        # Delete many-to-many connections with location groups and locations
        self.location = []
        self.location_group = []

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

        if commit:
            db.session.commit()
        return self

    def activate(self, commit: bool = True):
        self.activated = True
        self.deactivated_at = None
        if commit:
            db.session.commit()
        return self

    def deactivate(
        self, deactivated_at: datetime = datetime.utcnow(), commit: bool = True
    ):
        self.activated = False
        self.deactivated_at = deactivated_at
        if commit:
            db.session.commit()
        return self

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

    @hybrid_property
    def company_name(self):
        return self.company.name if self.company else None

    @company_name.expression
    def company_name(cls):
        return (
            select([Company.name]).where(cls.company_id == Company.id).scalar_subquery()
        )

    def __repr__(self):
        return f"<User: {self.username}>"


class AnonymousUser(AnonymousUserMixin):
    @property
    def permission(self):
        return UserPermissionLevel.ANONYMOUS


# NOTE option 1: set hashed password through model (flask-admin field only)
class UserView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "UserView"

    column_list = [
        "id",
        "username",
        "email",
        "role",
        "company_name",
        "activated",
        "last_time_online",
        "created_at",
    ]

    column_labels = {
        "password_hash": "Password",
    }

    column_searchable_list = column_list
    column_filters = column_list

    # Put span as description because it seems to be that
    # Flask-Admin doesn't provide an opportunity for field description style customization
    column_descriptions = dict(
        location_group="<span style='color: red'>**Choose one location group to provide user access to it.\
            Has higher priority than location, so if you select both (location and group)\
            user will have permission for the group!</span>",
        location="<span style='color: red'>**Choose one location to provide user access to it.</span>",
    )

    # To set order of the fields in form
    form_columns = (
        "username",
        "email",
        "password_hash",
        "role",
        "company",
        "location_group",
        "location",
        "activated",
        "created_at",
        "last_time_online",
    )

    form_excluded_columns = ("deleted_at", "is_deleted")

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
        delattr(form, "password_hash")

        form.company.query = self._available_companies(True).all()

        # Prevent global users from selecting location/groups from other companies (not selected one)
        if current_user.permission == UserPermissionLevel.GLOBAL and form.company.data:
            form.location_group.query_factory = lambda: LocationGroup.query.filter(
                LocationGroup.company_id == form.company.data.id
            )
            form.location.query_factory = lambda: Location.query.filter(
                Location.company_id == form.company.data.id
            )
        else:
            form.location_group.query_factory = self._available_location_groups
            form.location.query_factory = self._available_locations

        return form

    def create_form(self, obj=None):
        form = super(UserView, self).create_form(obj)
        form.company.query = self._available_companies(True).all()
        form.location_group.query_factory = self._available_location_groups
        form.location.query_factory = self._available_locations

        # Check if there is deleted user with such email and username
        deleted_user = (
            User.query.with_deleted()
            .filter_by(
                username=form.username.data,
                email=form.email.data,
                is_deleted=True,
            )
            .first()
        )
        if deleted_user:
            form.username.validators = form.username.validators[1:]
            form.email.validators = form.email.validators[1:]

        return form

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """

        # Check that selected company is active
        if form.activated.data:
            company = Company.query.filter_by(id=form.company.data.id).first()
            if not company.activated:
                flash(
                    gettext(
                        "Failed to create record. Company %(company)s is deactivated.",
                        company=company.name,
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Company {} is deactivated.", company.name
                )
                return False

        # If user has Location level permission, check that selected location is active
        if not form.location_group.data and form.location.data:
            location = Location.query.filter_by(id=form.location.data[0].id).first()
            if not location.activated:
                flash(
                    gettext(
                        "Failed to create record. Location %(location)s is deactivated.",
                        location=location.name,
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Location {} is deactivated.",
                    location.name,
                )

        # Check if there is deleted user with such email and username
        deleted_user = (
            User.query.with_deleted()
            .filter_by(
                username=form.username.data,
                email=form.email.data,
                is_deleted=True,
            )
            .first()
        )

        try:
            if deleted_user:
                # Restore user
                model = deleted_user
                original_created_at = model.created_at
                form.populate_obj(model)
                model.is_deleted = False
                model.deleted_at = None
                model.created_at = original_created_at

                if form.activated.data:
                    model.deactivated_at = None
                else:
                    model.deactivated_at = datetime.utcnow()

                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info("User {} was restored.", model.username)
            else:
                model = self.build_new_instance()

                form.populate_obj(model)

                if not form.activated.data:
                    model.deactivated_at = datetime.utcnow()

                self.session.add(model)
                self._on_model_change(form, model, True)
                self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to create record. %(error)s", error=str(ex)),
                    "error",
                )
                logger.error("Failed to create record.")

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form, model):
        """
        Update model from form.

        :param form:
            Form instance
        :param model:
            Model instance
        """
        # Check that selected company is active
        if form.activated.data:
            company = Company.query.filter_by(id=form.company.data.id).first()
            if not company.activated:
                flash(
                    gettext(
                        "Failed to update record. Company %(company)s is deactivated.",
                        company=company.name,
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Company {} is deactivated.", company.name
                )
                return False

        # If user has Location level permission, check that selected location is active
        if not form.location_group.data and form.location.data:
            location = Location.query.filter_by(id=form.location.data[0].id).first()
            if not location.activated:
                flash(
                    gettext(
                        "Failed to update record. Location %(location)s is deactivated.",
                        location=location.name,
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Location {} is deactivated.",
                    location.name,
                )

        try:
            # If user was deactivated
            if not form.activated.data and form.activated.data != model.activated:
                model.deactivated_at = datetime.utcnow()

            form.populate_obj(model)
            self._on_model_change(form, model, False)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to update record. %(error)s", error=str(ex)),
                    "error",
                )
                logger.error("Failed to update record.")

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def delete_model(self, model):
        """
        Soft deletion of model

        :param model:
            Model to delete
        """
        try:
            self.on_model_delete(model)
            self.session.flush()

            model.delete(commit=False)

            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to delete record. %(error)s", error=str(ex)),
                    "error",
                )
                logger.error("Failed to delete record.")

            self.session.rollback()

            return False
        else:
            self.after_model_delete(model)

        return True

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
                result_query = self.model.query.filter(
                    self.model.username != "emarsuperuser"
                )
            case UserPermissionLevel.COMPANY:
                result_query = self.model.query.filter(
                    self.model.company_id == current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                result_query = self.model.query.filter(
                    self.model.location_group.any(
                        LocationGroup.id.in_(
                            [group.id for group in current_user.location_group]
                        )
                    )
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.model.query.filter(
                    self.model.location.any(
                        Location.id.in_(
                            [location.id for location in current_user.location]
                        )
                    )
                )
            case _:
                result_query = self.model.query.filter(self.model.id == -1)

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()
        return actual_query.with_entities(func.count())

    def get_one(self, id):
        return self.model.query.filter_by(id=tools.iterdecode(id)).first()
