from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from sqlalchemy import sql, func, and_, or_
from sqlalchemy.orm import Query, relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from flask import flash
from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from flask_admin.contrib.sqla import tools
from flask_admin.babel import gettext

from app import db
from app.models.utils import (
    ModelMixin,
    RowActionListMixin,
    SoftDeleteMixin,
    QueryWithSoftDelete,
    ActivatedMixin,
)
from app.utils import MyModelView
from app.logger import logger
from .system_log import SystemLogType

from config import BaseConfig as CFG


class Company(db.Model, ModelMixin, SoftDeleteMixin, ActivatedMixin):
    __tablename__ = "companies"

    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(64), unique=True, nullable=False)
    default_sftp_username = db.Column(db.String(128))
    default_sftp_password = db.Column(db.String(128))
    locations_per_company = db.Column(db.Integer)
    total_computers = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pcc_org_id = db.Column(db.String(128), nullable=True)
    created_from_pcc = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )
    is_global = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )
    is_trial = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )

    users = relationship(
        "User",
        back_populates="company",
        lazy="select",
        primaryjoin="and_(Company.id == User.company_id, User.is_deleted.is_(False))",
    )

    locations = relationship(
        "Location",
        back_populates="company",
        lazy="select",
        primaryjoin="and_(Company.id == Location.company_id, Location.is_deleted.is_(False))",
    )

    location_groups = relationship(
        "LocationGroup",
        back_populates="company",
        lazy="select",
        primaryjoin="and_(Company.id == LocationGroup.company_id, LocationGroup.is_deleted.is_(False))",
    )

    computers = relationship(
        "Computer",
        back_populates="company",
        lazy="select",
        primaryjoin="and_(Company.id == Computer.company_id, Computer.is_deleted.is_(False))",
    )

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "default_sftp_username",
            "default_sftp_password",
            "locations_per_company",
            "total_computers",
            "computers_online",
            "computers_offline",
            "pcc_org_id",
        ]

    # NOTE: unfortunately, next callable properties can't be used with Flask Admin (as table columns)
    # Because initialization of CompanyView class is done before initialization of Computer/Location models
    # So, we use next properties for the email templates but we still need to have columns
    # "locations_per_company", "total_computers", "computers_online", "computers_offline" and task "update_cl_stat"
    # to update these columns

    def delete(self, commit: bool = True):
        """
        Soft delete the company

        Args:
            commit (bool, optional): Commit the changes. Defaults to True.

        Returns:
            Company: Company object
        """
        # Delete all the users associated with this company
        for user in self.users:
            user.delete(commit)

        # Delete all the location groups associated with this company
        for location in self.location_groups:
            location.delete(commit)

        # Delete all the locations associated with this company
        for location in self.locations:
            location.delete(commit)

        # Delete all the computers associated with this company
        for computer in self.computers:
            computer.delete(commit)

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

        if commit:
            db.session.commit()
        return self

    def restore(self, commit: bool = True):
        """
        Restore the company from soft deletion

        Args:
            commit (bool, optional): Commit the changes. Defaults to True.

        Returns:
            Company: Company object
        """
        self.locations_per_company = 0
        self.total_computers = 0
        self.computers_online = 0
        self.computers_offline = 0
        self.is_deleted = False
        self.deleted_at = None

        if commit:
            db.session.commit()
        return self

    def deactivate(self, commit: bool = True):
        """
        Deactivate the company

        Args:
            commit (bool, optional): Commit the changes. Defaults to True.

        Returns:
            Company: Company object
        """
        deactivation_time: datetime = datetime.utcnow()

        # Deactivate all active the users associated with this company
        for user in self.users:
            if user.activated:
                user.deactivate(deactivated_at=deactivation_time, commit=False)

        # Deactivate all the active locations associated with this company
        for location in self.locations:
            if location.activated:
                location.deactivate(deactivated_at=deactivation_time, commit=False)

        # Deactivate all the active computers associated with this company
        for computer in self.computers:
            if computer.activated:
                computer.deactivate(deactivated_at=deactivation_time, commit=False)

        self.activated = False
        self.deactivated_at = deactivation_time

        if commit:
            db.session.commit()
        return self

    def activate(self, commit: bool = True):
        """
        Activate the company

        Args:
            commit (bool, optional): Commit the changes. Defaults to True.

        Returns:
            Company: Company object
        """
        # Activate users associated with this company (if they were deactivated with company)
        for user in self.users:
            if user.deactivated_at == self.deactivated_at:
                user.activate(commit=False)

        # Activate locations associated with this company (if they were deactivated with company)
        for location in self.locations:
            if location.deactivated_at == self.deactivated_at:
                location.activate(commit=False)

        # Activate computers associated with this company (if they were deactivated with company)
        for computer in self.computers:
            if computer.deactivated_at == self.deactivated_at:
                computer.activate(commit=False)

        self.activated = True
        self.deactivated_at = None

        if commit:
            db.session.commit()
        return self

    @hybrid_property
    def total_computers_counter(self):
        """
        Total number of computers for this company (without deleted and not activated)

        Returns:
            int: total number of computers
        """
        from app.models.computer import Computer

        computers_number: int = Computer.query.filter(
            Computer.company_id == self.id,
            Computer.activated.is_(True),
        ).count()
        return computers_number

    @hybrid_property
    def total_computers_with_deleted(self):
        """
        Total number of computers for this company (with deleted and not activated)

        Returns:
            int: total number of computers
        """
        from app.models.computer import Computer

        computers_number: int = (
            Computer.query.with_deleted()
            .filter(
                Computer.company_id == self.id,
            )
            .count()
        )
        return computers_number

    @hybrid_property
    def total_locations_with_deleted(self):
        """
        Total number of locations for this company (with deleted)

        Returns:
            int: total number of locations
        """
        from app.models.location import Location

        locations_number: int = (
            Location.query.with_deleted()
            .filter(
                Location.company_id == self.id,
            )
            .count()
        )
        return locations_number

    @hybrid_property
    def total_users_with_deleted(self):
        """
        Total number of users for this company (with deleted)

        Returns:
            int: total number of users
        """
        from app.models.user import User

        users_number: int = (
            User.query.with_deleted().filter(User.company_id == self.id).count()
        )
        return users_number

    @hybrid_property
    def primary_computers_offline(self):
        """
        Total number of offline primary computers for this company (current moment)

        Returns:
            int: total number of offline primary computers
        """
        from app.models.computer import Computer, DeviceRole

        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        computers_number: int = Computer.query.filter(
            and_(
                Computer.company_id == self.id,
                Computer.activated.is_(True),
                Computer.device_role == DeviceRole.PRIMARY,
                or_(
                    Computer.last_download_time.is_(None),
                    Computer.last_download_time
                    < current_east_time - timedelta(hours=1),
                ),
            )
        ).count()

        return computers_number

    @hybrid_property
    def total_offline_computers(self):
        """
        Total number of offline computers for this company (current moment)

        Returns:
            int: total number of offline computers
        """
        from app.models.computer import Computer

        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        computers_number: int = Computer.query.filter(
            and_(
                Computer.company_id == self.id,
                Computer.activated.is_(True),
                or_(
                    Computer.last_download_time.is_(None),
                    Computer.last_download_time
                    < current_east_time - timedelta(hours=1),
                ),
            )
        ).count()

        return computers_number

    @hybrid_property
    def total_offline_locations(self):
        """
        Total number of offline locations for this company (current moment)

        Returns:
            int: total number of offline locations
        """
        from app.models.computer import Computer
        from app.models.location import Location

        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)
        offline_locations_counter: int = 0

        locations: list[Location] = self.locations

        for location in locations:
            activated_computers_query: Query = Computer.query.filter(
                Computer.location_id == location.id,
                Computer.activated.is_(True),
            )

            if not activated_computers_query.count():
                continue

            online_computers: list[Computer] = activated_computers_query.filter(
                Computer.last_download_time.is_not(None),
                Computer.last_download_time >= current_east_time - timedelta(hours=1),
            ).all()

            if not online_computers:
                offline_locations_counter += 1

        return offline_locations_counter

    @hybrid_method
    def total_pcc_api_calls(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Total number of PCC API calls from computers of this company (including deleted ones)

        Args:
            start_time (datetime): start time of the period
            end_time (datetime): end time of the period

        Returns:
            int: total number of PCC API calls
        """
        from app.models.computer import Computer
        from app.models.download_backup_call import DownloadBackupCall

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        # Retrieve all the computers (even deleted ones) for this company
        computers = (
            Computer.query.with_deleted().filter(Computer.company_id == self.id).all()
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
        """
        Total number of alert events from locations of this company (including deleted ones)

        Args:
            start_time (datetime, optional): start time of the period.
                Defaults to datetime.utcnow() - timedelta(days=30).
            end_time (datetime, optional): end time of the period.

        Returns:
            int: total number of alert events
        """
        from app.models.location import Location
        from app.models.alert_event import AlertEvent

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        # Retrieve all the company locations (even deleted ones)
        locations: list[Location] = (
            Location.query.with_deleted().filter(Location.company_id == self.id).all()
        )
        location_ids: list[int] = [location.id for location in locations]
        total_alert_events: int = AlertEvent.query.filter(
            AlertEvent.location_id.in_(location_ids),
            AlertEvent.created_at >= start_time,
            AlertEvent.created_at <= end_time,
        ).count()

        return total_alert_events


class CompanyView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "CompanyView"

    list_template = "import-company_location-to-dashboard.html"

    column_list = [
        "name",
        "default_sftp_username",
        "locations_per_company",
        "total_computers",
        "computers_online",
        "computers_offline",
        "pcc_org_id",
        "created_from_pcc",
    ]

    column_labels = dict(
        pcc_org_id="PointClickCare Org ID",
        created_from_pcc="Created from PointClickCare",
    )

    column_filters = column_list

    column_searchable_list = column_list

    action_disallowed_list = ["delete"]

    # To set order of the fields in form
    form_columns = (
        "name",
        "is_trial",
        "default_sftp_username",
        "default_sftp_password",
        "locations_per_company",
        "total_computers",
        "computers_online",
        "computers_offline",
        "created_at",
        "pcc_org_id",
    )

    form_excluded_columns = (
        "created_from_pcc",
        "locations",
        "is_global",
        "users",
        "computers",
        "is_deleted",
        "deleted_at",
        "location_groups",
    )

    form_widget_args = {
        "locations_per_company": {"readonly": True},
        "total_computers": {"readonly": True},
        "computers_online": {"readonly": True},
        "computers_offline": {"readonly": True},
        "created_at": {"readonly": True},
    }

    form_args = {
        "is_trial": {"label": "eMAR Vault Lite Edition"},
    }

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def is_accessible(self):
        from .user import UserPermissionLevel

        return current_user.permission.value in [
            UserPermissionLevel.GLOBAL.value,
            UserPermissionLevel.COMPANY.value,
        ]

    def _can_edit(self, model):
        from .user import UserPermissionLevel, UserRole

        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
            and not model.is_global
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
        from .user import UserPermissionLevel, UserRole

        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
            and not model.is_global
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

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """

        # Check if there is deleted company with such name
        deleted_company = (
            Company.query.with_deleted()
            .filter_by(
                name=form.name.data,
                is_deleted=True,
            )
            .first()
        )

        try:
            if deleted_company:
                # Restore company
                model = deleted_company
                original_created_at = model.created_at
                form.populate_obj(model)
                model.is_deleted = False
                model.deleted_at = None
                model.created_at = original_created_at
                model.created_from_pcc = False
                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info(f"Company {model.name} was restored.")
            else:
                model = self.build_new_instance()

                form.populate_obj(model)
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
        from app.models.computer import Computer, DeviceRole

        try:
            # If company changed to trial - deactivate computers in its locations
            if form.is_trial.data and not model.is_trial:
                for location in model.locations:
                    primary_active_computer = Computer.query.filter(
                        Computer.location_id == location.id,
                        Computer.device_role == DeviceRole.PRIMARY,
                        Computer.activated.is_(True),
                    ).first()
                    any_active_computer = Computer.query.filter(
                        Computer.location_id == location.id,
                        Computer.activated.is_(True),
                    ).first()

                    if not primary_active_computer and not any_active_computer:
                        continue

                    for computer in location.computers:
                        if (
                            primary_active_computer
                            and computer.id == primary_active_computer.id
                        ):
                            continue
                        elif (
                            not primary_active_computer
                            and computer.id == any_active_computer.id
                        ):
                            continue

                        computer.activated = False

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

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that company was created or updated
        if is_created:
            create_system_log(SystemLogType.COMPANY_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.COMPANY_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that company was deleted
        create_system_log(SystemLogType.COMPANY_DELETED, model, current_user)

    def get_query(self):
        from .user import UserPermissionLevel, UserRole

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
                    self.model.id == current_user.company_id
                )
            case _:
                result_query = self.model.query.filter(self.model.id == -1)

        return result_query.filter(self.model.is_global.is_(False))

    def get_count_query(self):
        actual_query = self.get_query()
        return actual_query.with_entities(func.count())

    def get_one(self, id):
        return self.model.query.filter_by(id=tools.iterdecode(id)).first()
