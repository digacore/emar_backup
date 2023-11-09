import enum
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from sqlalchemy import func, sql, select, or_, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from flask import flash
from flask_login import current_user
from flask_admin.babel import gettext
from flask_admin.model.template import EditRowAction, DeleteRowAction
from flask_admin.form import Select2Widget
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.contrib.sqla import tools

from wtforms import validators

from app import db
from app.models.utils import (
    ModelMixin,
    RowActionListMixin,
    SoftDeleteMixin,
    QueryWithSoftDelete,
)
from app.utils import MyModelView
from app.logger import logger
from .company import Company
from .system_log import SystemLogType

from config import BaseConfig as CFG


class LocationStatus(enum.Enum):
    ONLINE = "ONLINE"
    ONLINE_PRIMARY_OFFLINE = "ONLINE_PRIMARY_OFFLINE"
    OFFLINE = "OFFLINE"


class Location(db.Model, ModelMixin, SoftDeleteMixin):
    __tablename__ = "locations"

    __table_args__ = (db.UniqueConstraint("company_id", "name"),)

    # NOTE this is needed to filter soft deleted records
    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    name = db.Column(db.String(64), nullable=False)
    status = db.Column(Enum(LocationStatus), nullable=True)
    default_sftp_path = db.Column(db.String(256))
    computers_per_location = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pcc_fac_id = db.Column(db.Integer, nullable=True)
    use_pcc_backup = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )
    created_from_pcc = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )

    company = relationship(
        "Company",
        back_populates="locations",
        lazy="select",
    )

    alert_events = relationship(
        "AlertEvent",
        back_populates="location",
        lazy="select",
    )

    computers = relationship(
        "Computer",
        back_populates="location",
        lazy="select",
        primaryjoin="and_(Location.id == Computer.location_id, Computer.is_deleted.is_(False))",
    )

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "company_id",
            "default_sftp_path",
            "computers_per_location",
            "computers_online",
            "computers_offline",
            "pcc_fac_id",
            "use_pcc_backup",
        ]

    def delete(self, commit: bool = True):
        # Mark all the location computers and location itself as deleted
        for computer in self.computers:
            computer.delete(commit=False)

        # Remove location from location group
        self.group = []

        # Delete users which have access only to this location
        for user in self.users:
            # If user connected to some location group - just remove connection to this location
            if user.location_group:
                user.location = []
            # Else delete user
            else:
                user.delete(commit=False)

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

        if commit:
            db.session.commit()
        return self

    @hybrid_property
    def company_name(self):
        return self.company.name

    @company_name.expression
    def company_name(cls):
        return select([Company.name]).where(cls.company_id == Company.id).as_scalar()

    @company_name.setter
    def company_name(self, value):
        new_company = Company.query.filter_by(name=value).first()

        if not new_company:
            raise ValueError(f"Company with name {value} doesn't exist")

        self.company_id = new_company.id

    # NOTE: unfortunately, next callable properties can't be used with Flask Admin (as table columns)
    # Because initialization of LocationView class is done before initialization of Compute model
    # So, we use next properties for the email templates but we still need to have columns
    # "computers_per_location", "computers_online", "computers_offline" and task "update_cl_stat"
    # to update these columns

    @hybrid_property
    def total_computers(self) -> int:
        from app.models.computer import Computer

        return Computer.query.filter(
            Computer.location_id == self.id,
            Computer.activated.is_(True),
        ).count()

    @hybrid_property
    def total_computers_offline(self) -> int:
        from app.models.computer import Computer

        time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        return Computer.query.filter(
            Computer.location_id == self.id,
            Computer.activated.is_(True),
            or_(
                Computer.last_download_time.is_(None),
                Computer.last_download_time < time - timedelta(hours=1),
            ),
        ).count()

    @hybrid_property
    def primary_computers_offline(self) -> int:
        from app.models.computer import Computer, DeviceRole

        time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        return Computer.query.filter(
            Computer.location_id == self.id,
            Computer.activated.is_(True),
            Computer.device_role == DeviceRole.PRIMARY,
            or_(
                Computer.last_download_time.is_(None),
                Computer.last_download_time < time - timedelta(hours=1),
            ),
        ).count()

    @hybrid_method
    def total_pcc_api_calls(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        from app.models.computer import Computer
        from app.models.download_backup_call import DownloadBackupCall

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        # Retrieve all the computers (even deleted ones) for this location
        computers: list[Computer] = (
            Computer.query.with_deleted().filter(Computer.location_id == self.id).all()
        )
        computers_ids: list[int] = [comp.id for comp in computers]
        total_pcc_api_calls: int = DownloadBackupCall.query.filter(
            DownloadBackupCall.computer_id.in_(computers_ids),
            DownloadBackupCall.created_at >= start_time,
            DownloadBackupCall.created_at <= end_time,
        ).count()

        return total_pcc_api_calls

    @hybrid_method
    def total_alert_events(
        self,
        start_time: datetime = datetime.utcnow() - timedelta(days=30),
        end_time: datetime = datetime.utcnow(),
    ) -> int:
        from app.models.alert_event import AlertEvent

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        total_alert_events: int = AlertEvent.query.filter(
            AlertEvent.location_id == self.id,
            AlertEvent.created_at >= start_time,
            AlertEvent.created_at <= end_time,
        ).count()

        return total_alert_events


class LocationView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "LocationView"

    list_template = "import-company_location-to-dashboard.html"

    column_hide_backrefs = False
    column_list = [
        "name",
        "company_name",
        "status",
        "computers_per_location",
        "computers_online",
        "computers_offline",
        "default_sftp_path",
        "pcc_fac_id",
        "use_pcc_backup",
        "created_from_pcc",
    ]

    column_labels = dict(
        pcc_fac_id="PointClickCare Facility ID",
        use_pcc_backup="Use PointClickCare Backup",
        created_from_pcc="Created from PointClickCare",
    )

    column_searchable_list = column_list
    column_filters = column_list
    column_sortable_list = column_list
    action_disallowed_list = ["delete"]

    form_widget_args = {
        "computers_per_location": {"readonly": True},
        "total_computers": {"readonly": True},
        "computers_online": {"readonly": True},
        "computers_offline": {"readonly": True},
        "created_at": {"readonly": True},
    }

    # To set order of the fields in form
    form_columns = (
        "company",
        "name",
        "default_sftp_path",
        "computers_per_location",
        "computers_online",
        "computers_offline",
        "created_at",
        "pcc_fac_id",
        "use_pcc_backup",
        "group",
    )

    form_excluded_columns = (
        "created_from_pcc",
        "users",
        "status",
        "alert_events",
        "computers",
    )

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def _can_edit(self, model):
        from app.models.user import UserPermissionLevel, UserRole

        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
        from app.models.user import UserPermissionLevel, UserRole

        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
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

    # All these manipulations with group field are needed because
    # between Location and LocationGroup many-to-many relationship (Location can have only one group or no group)
    # But Flask-Admin builds form for many-to-many relationship as SelectMultipleField (we need SelectField)
    def get_create_form(self):
        form = super().get_create_form()
        form.group = QuerySelectField(
            "Group",
            validators=[validators.Optional()],
            allow_blank=True,
        )

        return form

    def create_form(self, obj=None):
        form = super().create_form(obj)

        form.company.query_factory = self._available_companies

        form.group.widget = Select2Widget()
        form.group.query_factory = self._available_location_groups

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        # apply a sort to the relation
        form.company.query_factory = self._available_companies
        form.group.query_factory = self._available_location_groups

        return form

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """

        # Check if there is deleted location with such name and for such company
        deleted_location = (
            Location.query.with_deleted()
            .filter_by(
                name=form.name.data,
                company_id=form.company.data.id,
                is_deleted=True,
            )
            .first()
        )

        group_data = form.group.data
        del form.group

        try:
            if deleted_location:
                # Restore location
                model = deleted_location
                original_created_at = model.created_at
                form.populate_obj(model)
                model.is_deleted = False
                model.deleted_at = None
                model.created_at = original_created_at
                model.created_from_pcc = False
                model.group = [group_data] if group_data else []
                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info(f"Location {model.name} was restored.")
            else:
                model = self.build_new_instance()

                form.populate_obj(model)
                model.group = [group_data] if group_data else []
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

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that location was created or updated
        if is_created:
            create_system_log(SystemLogType.LOCATION_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.LOCATION_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that location was deleted
        create_system_log(SystemLogType.LOCATION_DELETED, model, current_user)

    def get_query(self):
        from app.models.user import UserPermissionLevel, UserRole

        # NOTE handle permissions - meaning which details current user could view
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            if "delete" in self.action_disallowed_list:
                self.action_disallowed_list.remove("delete")
            self.can_create = True
        else:
            if "delete" not in self.action_disallowed_list:
                self.action_disallowed_list.append("delete")
            self.can_create = False

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                result_query = self.model.query
            case UserPermissionLevel.COMPANY:
                result_query = self.model.query.filter(
                    self.model.company_id == current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                locations = current_user.location_group[0].locations
                result_query = self.model.query.filter(
                    self.model.id.in_([location.id for location in locations])
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.model.query.filter(
                    self.model.id == current_user.location[0].id
                )
            case _:
                result_query = self.model.query.filter(self.model.id == -1)

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        return actual_query.with_entities(func.count())

    def get_one(self, id):
        return self.model.query.filter_by(id=tools.iterdecode(id)).first()
