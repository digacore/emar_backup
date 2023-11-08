import enum
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from sqlalchemy import JSON, or_, and_, sql, func, select, Enum, case
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from flask_admin.babel import gettext
from flask_admin.model.template import EditRowAction, DeleteRowAction

from flask import flash
from flask_login import current_user

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView
from app.logger import logger

from .desktop_client import DesktopClient
from .user import UserPermissionLevel, UserRole
from .company import Company
from .location import Location
from .system_log import SystemLogType
from .utils import SoftDeleteMixin, QueryWithSoftDelete

from config import BaseConfig as CFG


# TODO add to all models secure form? csrf
# from flask_admin.form import SecureForm
# from flask_admin.contrib.sqla import ModelView

# class CarAdmin(ModelView):
#     form_base_class = SecureForm


class DeviceType(enum.Enum):
    LAPTOP = "LAPTOP"
    DESKTOP = "DESKTOP"


class DeviceRole(enum.Enum):
    PRIMARY = "PRIMARY"
    ALTERNATE = "ALTERNATE"


class ComputerStatus(enum.Enum):
    ONLINE = "ONLINE"
    ONLINE_NO_BACKUP = "ONLINE_NO_BACKUP"
    OFFLINE_NO_BACKUP = "OFFLINE_NO_BACKUP"
    NOT_ACTIVATED = "NOT_ACTIVATED"


class Computer(db.Model, ModelMixin, SoftDeleteMixin):
    __tablename__ = "computers"

    # NOTE this is needed to use soft delete
    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id", ondelete="CASCADE"), nullable=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    computer_name = db.Column(db.String(64), unique=True, nullable=False)
    sftp_host = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_HOST)
    sftp_username = db.Column(db.String(64), default=CFG.DEFAULT_SFTP_USERNAME)
    sftp_password = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_PASSWORD)
    sftp_folder_path = db.Column(db.String(256))
    folder_password = db.Column(db.String(128), default=CFG.DEFAULT_FOLDER_PASSWORD)

    type = db.Column(db.String(128))
    device_type = db.Column(Enum(DeviceType), nullable=True)
    device_role = db.Column(
        Enum(DeviceRole),
        nullable=False,
        default=DeviceRole.PRIMARY,
        server_default=sql.text("'PRIMARY'"),
    )
    msi_version = db.Column(db.String(64), default="stable")
    current_msi_version = db.Column(db.String(64))

    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="new_computer", nullable=False)

    manager_host = db.Column(db.String(256), default=CFG.DEFAULT_MANAGER_HOST)
    # Place where backup file was downloaded last time (tempdir)
    last_downloaded = db.Column(db.String(256))
    # Place where backup file was saved last time (directory inside emar_backups.zip)
    last_saved_path = db.Column(db.String(256))
    files_checksum = db.Column(JSON)
    # TODO do we need this one? Could computer be deactivated?
    activated = db.Column(db.Boolean, default=False)

    logs_enabled = db.Column(db.Boolean, server_default=sql.true(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    computer_ip = db.Column(db.String(128))

    last_time_logs_enabled = db.Column(db.DateTime, default=datetime.now)
    last_time_logs_disabled = db.Column(db.DateTime)

    company = relationship(
        "Company",
        back_populates="computers",
        lazy="select",
    )

    location = relationship(
        "Location",
        back_populates="computers",
        lazy="select",
    )

    backup_logs = relationship("BackupLog", lazy="select")

    download_backup_calls = relationship(
        "DownloadBackupCall",
        lazy="select",
    )

    log_events = relationship("LogEvent", lazy="select")

    def __repr__(self):
        return self.computer_name

    def _cols(self):
        return [
            "computer_name",
            "company_id",
            "location_id",
            "download_status",
            "last_download_time",
            "last_time_online",
            "msi_version",
            "current_msi_version",
            "sftp_host",
            "sftp_username",
            "sftp_folder_path",
            "type",
            "device_type",
            "device_role",
            "manager_host",
            "activated",
            "logs_enabled",
            "files_checksum",
            "identifier_key",
            "computer_ip",
        ]

    @hybrid_property
    def location_name(self):
        return self.location.name if self.location else None

    @location_name.expression
    def location_name(cls):
        return select([Location.name]).where(cls.location_id == Location.id).as_scalar()

    @location_name.setter
    def location_name(self, value):
        new_location = Location.query.filter_by(name=value).first()
        self.location_id = new_location.id if new_location else None

    @hybrid_property
    def company_name(self):
        return self.company.name if self.company else None

    @company_name.expression
    def company_name(cls):
        return select([Company.name]).where(cls.company_id == Company.id).as_scalar()

    @company_name.setter
    def company_name(self, value):
        new_company = Company.query.filter_by(name=value).first()
        self.company_id = new_company.id if new_company else None

    @hybrid_property
    def status(self) -> ComputerStatus:
        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        # Not activated status
        if not self.activated:
            return ComputerStatus.NOT_ACTIVATED
        # If computer downloaded backup less than 1 hour ago - it is ONLINE
        elif (
            db.session.query(Computer)
            .filter(
                Computer.id == self.id,
                Computer.last_download_time.is_not(None),
                Computer.last_download_time >= current_east_time - timedelta(hours=1),
            )
            .first()
        ):
            return ComputerStatus.ONLINE
        # If computer downloaded backup more than 1 hour ago but was online less than 10 minutes ago - ONLINE_NO_BACKUP
        elif (
            db.session.query(Computer)
            .filter(
                Computer.id == self.id,
                Computer.last_time_online.is_not(None),
                Computer.last_time_online >= current_east_time - timedelta(minutes=10),
            )
            .first()
        ):
            return ComputerStatus.ONLINE_NO_BACKUP
        else:
            return ComputerStatus.OFFLINE_NO_BACKUP

    @status.expression
    def status(cls):
        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        return case(
            [
                (
                    cls.activated.is_(False),
                    ComputerStatus.NOT_ACTIVATED.value.replace("_", " "),
                ),
                (
                    and_(
                        cls.last_download_time.is_not(None),
                        cls.last_download_time
                        >= current_east_time - timedelta(hours=1),
                    ),
                    ComputerStatus.ONLINE.value,
                ),
                (
                    and_(
                        cls.last_time_online.is_not(None),
                        cls.last_time_online
                        >= current_east_time - timedelta(minutes=10),
                    ),
                    ComputerStatus.ONLINE_NO_BACKUP.value.replace("_", " "),
                ),
            ],
            else_=ComputerStatus.OFFLINE_NO_BACKUP.value.replace("_", " "),
        )

    @hybrid_property
    def location_status(self):
        return self.location.status if self.location else None

    @hybrid_property
    def offline_period(self) -> int:
        """
        Returns current offline period of computer in last day or 24 hours

        Args:
            time (datetime, optional): current east time
        Returns:
            int: offline period in hours
        """
        time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        if not self.last_download_time:
            return 24
        else:
            if (time - self.last_download_time).days:
                return 24
            else:
                return (time - self.last_download_time).seconds // 3600

    @hybrid_property
    def last_week_offline_occurrences(self) -> int:
        from app.models.backup_log import BackupLog, BackupLogType

        """
        Returns number of occurrences offline in last week

        Returns:
            int: number of occurrences
        """
        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        # If computer backup logs disables - return None
        if not self.logs_enabled:
            return None

        last_log: BackupLog = (
            BackupLog.query.filter(
                BackupLog.computer_id == self.id,
            )
            .order_by(BackupLog.end_time.desc())
            .first()
        )

        # If computer doesn't have any logs or the last one older than 7 days - return 1
        if not last_log or last_log.end_time < current_east_time - timedelta(days=7):
            return 1

        last_week_offline_logs: int = BackupLog.query.filter(
            BackupLog.computer_id == self.id,
            BackupLog.backup_log_type == BackupLogType.NO_DOWNLOADS_PERIOD,
            BackupLog.end_time >= current_east_time - timedelta(days=7),
        ).count()

        return last_week_offline_logs

    @hybrid_property
    def last_week_offline_time(self) -> timedelta:
        from app.models.backup_log import BackupLog, BackupLogType

        """
        Returns summarized offline time during the last week (timedelta object)

        Returns:
            timedelta: summarized offline time
        """
        current_east_time: datetime = CFG.offset_to_est(datetime.utcnow(), True)

        # If computer backup logs disables - return None
        if not self.logs_enabled:
            return None

        last_log: BackupLog = (
            BackupLog.query.filter(
                BackupLog.computer_id == self.id,
            )
            .order_by(BackupLog.end_time.desc())
            .first()
        )

        # If computer doesn't have any logs or the last one older than 7 days - 7 days timedelta
        if not last_log or last_log.end_time < current_east_time - timedelta(days=7):
            return timedelta(days=7)

        last_week_offline_logs: list[BackupLog] = (
            BackupLog.query.filter(
                BackupLog.computer_id == self.id,
                BackupLog.backup_log_type == BackupLogType.NO_DOWNLOADS_PERIOD,
                BackupLog.end_time >= current_east_time - timedelta(days=7),
            )
            .order_by(BackupLog.end_time.desc())
            .all()
        )

        summarized_offline_time: timedelta = timedelta(seconds=0)

        for log in last_week_offline_logs:
            # If log is still in progress - end time is current time
            if log == last_log:
                log.end_time = current_east_time

            if log.start_time < current_east_time - timedelta(days=7):
                summarized_offline_time += log.end_time - (
                    current_east_time - timedelta(days=7)
                )
            else:
                summarized_offline_time += log.duration

        return summarized_offline_time

    @hybrid_method
    def total_pcc_api_calls(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        from app.models.download_backup_call import DownloadBackupCall

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        total_pcc_api_calls: int = DownloadBackupCall.query.filter(
            DownloadBackupCall.computer_id == self.id,
            DownloadBackupCall.created_at >= start_time,
            DownloadBackupCall.created_at <= end_time,
        ).count()

        return total_pcc_api_calls


class ComputerView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ComputerView"

    list_template = "import-computer-to-dashboard.html"

    column_hide_backrefs = False
    column_list = [
        "computer_name",
        "status",
        "company_name",
        "location_name",
        "location_status",
        "device_role",
        "device_type",
        "last_download_time",
        "last_time_online",
        "computer_ip",
    ]

    searchable_sortable_list = [
        "computer_name",
        "status",
        "company_name",
        "location_name",
        "device_type",
        "device_role",
        "last_download_time",
        "last_time_online",
        "computer_ip",
    ]

    form_excluded_columns = (
        "log_events",
        "backup_logs",
        "last_time_logs_enabled",
        "last_time_logs_disabled",
        "download_backup_calls",
        "is_deleted",
        "deleted_at",
    )

    column_searchable_list = searchable_sortable_list
    column_sortable_list = searchable_sortable_list
    column_filters = searchable_sortable_list

    # NOTE allows edit in list view, but has troubles with permissions
    # column_editable_list = [
    #     # "computer_name",
    #     "company",
    #     # "location",
    #     # "type",
    #     # "sftp_host",
    #     # "sftp_username",
    #     # "sftp_folder_path",
    #     # "manager_host",
    # ]

    # TODO uncomment files_checksum when ready to go on
    form_widget_args = {
        "last_download_time": {"readonly": True},
        "last_time_online": {"readonly": True},
        "identifier_key": {"readonly": True},
        "created_at": {"readonly": True},
        "download_status": {"readonly": True},
        "last_downloaded": {"readonly": True},
        "last_saved_path": {"readonly": True},
        "current_msi_version": {"readonly": True},
        "computer_ip": {"readonly": True},
        "type": {"readonly": True},
        # "files_checksum": {"readonly": True},
    }

    # form_args control fields order. It is dict though...
    form_args = {
        "computer_name": {"label": "Computer name"},
        "company_id": {"label": "Company id", "id": "company_id"},
        "location_id": {"label": "Location id", "id": "location_id"},
        "sftp_host": {"label": "SFTP host"},
        "sftp_username": {"label": "SFTP username"},
        "sftp_password": {"label": "SFTP password"},
        "sftp_folder_path": {"label": "SFTP folder path"},
        "type": {"label": "Type"},
        "device_type": {"label": "Device type"},
        "device_role": {"label": "Device role"},
        "msi_version": {"label": "Msi version"},
        "current_msi_version": {"label": "Current msi version"},
        "manager_host": {"label": "Manager host"},
        "activated": {"label": "Activated"},
        "logs_enabled:": {"label": "Logs enabled"},
        "download_status": {"label": "Download status"},
        "last_download_time": {"label": "Last download time"},
        "last_time_online": {"label": "Last time online"},
        "identifier_key": {"label": "Identifier key"},
        "files_checksum": {"label": "Files checksum"},
        "created_at": {"label": "Created at"},
        "computer_ip": {"label": "Computer IP"},
    }

    form_choices = {"msi_version": CFG.CLIENT_VERSIONS}

    action_disallowed_list = ["delete"]

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def _can_edit(self, model):
        # return True to allow edit
        if current_user.role == UserRole.ADMIN:
            return True
        else:
            return False

    def _can_delete(self, model):
        if current_user.role == UserRole.ADMIN:
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

    def create_form(self, obj=None):
        form = super().create_form(obj)

        # Put only available for user companies and locations in the select field
        form.company.query_factory = self._available_companies
        form.location.query_factory = self._available_locations

        # Remove unique validator from computer_name field if deleted computer with such name exists
        deleted_computer = (
            Computer.query.with_deleted()
            .filter_by(
                computer_name=form.computer_name.data,
                is_deleted=True,
            )
            .first()
        )
        if deleted_computer:
            form.computer_name.validators = form.computer_name.validators[1:]

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        # Remember the prev value of the field logs_enabled
        self.logs_enabled_prev_value = obj.logs_enabled

        # Put only available for user companies and locations in the select field
        form.company.query_factory = self._available_companies

        if current_user.permission == UserPermissionLevel.GLOBAL and form.company.data:
            form.location.query = Location.query.filter_by(
                company_id=form.company.data.id
            ).all()
        else:
            form.location.query_factory = self._available_locations

        return form

    def on_model_change(self, form, model, is_created):
        if not is_created and self.logs_enabled_prev_value != model.logs_enabled:
            if model.logs_enabled:
                model.last_time_logs_enabled = datetime.utcnow()
            else:
                model.last_time_logs_disabled = datetime.utcnow()

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """
        try:
            # Check if there is deleted computer with such name
            deleted_computer = (
                Computer.query.with_deleted()
                .filter_by(
                    computer_name=form.computer_name.data,
                    is_deleted=True,
                )
                .first()
            )

            if deleted_computer:
                # Restore computer
                model = deleted_computer
                original_created_at = model.created_at
                form.populate_obj(model)
                model.is_deleted = False
                model.deleted_at = None
                model.created_at = original_created_at
                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info(f"Computer {model.computer_name} was restored.")
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

    def delete_model(self, model):
        """
        Soft deletion of model

        :param model:
            Model to delete
        """
        try:
            self.on_model_delete(model)
            self.session.flush()

            # Deactivate computer and logs. Then delete it
            model.activated = False
            model.logs_enabled = False
            model.is_deleted = True
            model.deleted_at = datetime.utcnow()

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

        # Create system log that computer was created or updated
        if is_created:
            create_system_log(SystemLogType.COMPUTER_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.COMPUTER_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that computer was deleted
        create_system_log(SystemLogType.COMPUTER_DELETED, model, current_user)

    def get_query(self):
        OBLIGATORY_VERSIONS = [
            ("stable", "stable"),
            ("latest", "latest"),
        ]

        versions = [
            i.version
            for i in DesktopClient.query.with_entities(DesktopClient.version).all()
        ]

        # remove old versions from global versions variable
        for version in CFG.CLIENT_VERSIONS:
            if version[0] not in versions or version not in OBLIGATORY_VERSIONS:
                CFG.CLIENT_VERSIONS.remove(version)

        # add new versions to global versions variable
        for version in versions:
            if (version, version) not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append((version, version))
        for dversion in OBLIGATORY_VERSIONS:
            if dversion not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append(dversion)

        # NOTE handle permissions - meaning which details current user could view
        self.form_choices = CFG.CLIENT_VERSIONS

        if current_user.role == UserRole.ADMIN:
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
                    or_(
                        self.model.company_id == current_user.company_id,
                        self.model.location_id.in_(
                            [loc.id for loc in current_user.company.locations]
                        ),
                    )
                )
            case UserPermissionLevel.LOCATION_GROUP:
                result_query = self.model.query.filter(
                    self.model.location_id.in_(
                        [loc.id for loc in current_user.location_group[0].locations]
                    )
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.model.query.filter(
                    self.model.location_id == current_user.location[0].id
                )
            case _:
                result_query = self.model.query.filter(self.model.id == -1)

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        return actual_query.with_entities(func.count())
