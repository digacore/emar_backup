import enum
from copy import copy
from datetime import datetime, timedelta

from flask import flash
from flask_admin.babel import gettext
from flask_admin.contrib.sqla import tools
from flask_admin.model.template import DeleteRowAction, EditRowAction
from flask_login import current_user
from sqlalchemy import JSON, Enum, and_, case, func, or_, select, sql
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from zoneinfo import ZoneInfo

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

from .additional_location import AdditionalLocation
from config import BaseConfig as CFG

from .company import Company
from .desktop_client import DesktopClient
from .location import Location
from .system_log import SystemLogType
from .user import UserPermissionLevel, UserRole

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


class PrinterStatus(enum.Enum):
    NORMAL = "NORMAL"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class Computer(db.Model, ModelMixin, SoftDeleteMixin, ActivatedMixin):
    __tablename__ = "computers"

    # NOTE this is needed to filter soft deleted records
    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    computer_name = db.Column(db.String(64), unique=True, nullable=False)
    sftp_host = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_HOST)
    sftp_port = db.Column(
        db.Integer,
        server_default=CFG.DEFAULT_SFTP_PORT,
        default=CFG.DEFAULT_SFTP_PORT,
    )
    sftp_username = db.Column(db.String(64), default=CFG.DEFAULT_SFTP_USERNAME)
    sftp_password = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_PASSWORD)
    sftp_folder_path = db.Column(db.String(256))
    additional_sftp_folder_paths = db.Column(db.String(256))
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

    logs_enabled = db.Column(db.Boolean, server_default=sql.true(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    computer_ip = db.Column(db.String(128))

    last_time_logs_enabled = db.Column(db.DateTime, default=datetime.utcnow)
    last_time_logs_disabled = db.Column(db.DateTime)

    printer_name = db.Column(db.String(128), default="")
    printer_status = db.Column(
        Enum(PrinterStatus),
        nullable=True,
        default=PrinterStatus.UNKNOWN,
        server_default=sql.text("'UNKNOWN'"),
    )
    printer_status_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    additional_locations = relationship(
        "AdditionalLocation",
        back_populates="computer",
    )

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

    backup_logs = relationship("BackupLog", back_populates="computer", lazy="select")

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
            "sftp_port",
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

    def delete(self, commit: bool = True):
        """Soft delete computer"""
        self.activated = False
        self.deactivated_at = datetime.utcnow()
        self.logs_enabled = False
        self.last_time_logs_disabled = datetime.utcnow()
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if commit:
            db.session.commit()
        return self

    def restore(self):
        """Restore computer from soft delete"""
        # Check that computer location and company still exist
        if (
            self.location_id
            and not Location.query.filter_by(id=self.location_id).first()
        ):
            self.location_id = None

        if self.company_id and not Company.query.filter_by(id=self.company_id).first():
            self.company_id = None

        self.is_deleted = False
        self.deleted_at = None
        self.current_msi_version = None
        self.download_status = None
        self.last_downloaded = None
        self.last_saved_path = None
        self.files_checksum = "{}"
        self.computer_ip = None
        db.session.commit()
        return self

    def activate(self, commit: bool = True):
        """Activate computer"""
        self.activated = True
        self.deactivated_at = None
        self.logs_enabled = True
        self.last_time_logs_enabled = datetime.utcnow()

        if commit:
            db.session.commit()
        return self

    def deactivate(
        self, deactivated_at: datetime = datetime.utcnow(), commit: bool = True
    ):
        """Deactivate computer"""
        self.activated = False
        self.deactivated_at = deactivated_at
        self.logs_enabled = False
        self.last_time_logs_disabled = deactivated_at

        if commit:
            db.session.commit()
        return self

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

    @property
    def get_additional_locations(self) -> list[Location]:
        return [al.location for al in self.additional_locations]

    @hybrid_property
    def is_company_trial(self):
        return self.company.is_trial if self.company else None

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
                Computer.last_download_time
                >= current_east_time - timedelta(hours=1, minutes=30),
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
                        >= current_east_time - timedelta(hours=1, minutes=30),
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
        Returns current offline period of computer in last day

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
        """
        Returns total number of PCC API calls during the specified period

        Args:
            start_time (datetime): start of the period
            end_time (datetime): end of the period

        Returns:
            int: total number of PCC API calls
        """
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
    edit_template = "import-edit-computer.html"
    can_create = False

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
        "printer_name",
        "printer_status",
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

    # To set order of the fields in form
    form_columns = (
        "company",
        "location",
        "additional_locations",
        "computer_name",
        "activated",
        "logs_enabled",
        "sftp_host",
        "sftp_port",
        "sftp_username",
        "sftp_password",
        "sftp_folder_path",
        "additional_sftp_folder_paths",
        "folder_password",
        "type",
        "device_type",
        "device_role",
        "msi_version",
        "current_msi_version",
        "download_status",
        "last_download_time",
        "last_time_online",
        "identifier_key",
        "manager_host",
        "last_downloaded",
        "last_saved_path",
        "files_checksum",
        "created_at",
        "computer_ip",
    )

    form_excluded_columns = (
        "log_events",
        "backup_logs",
        "last_time_logs_enabled",
        "last_time_logs_disabled",
        "download_backup_calls",
        "is_deleted",
        "deleted_at",
        "deactivated_at",
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
        "sftp_port": {"readonly": True},
        # "files_checksum": {"readonly": True},
    }

    # form_args control fields order. It is dict though...
    form_args = {
        "computer_name": {"label": "Computer name"},
        "company_id": {"label": "Company id", "id": "company_id"},
        "location_id": {"label": "Location id", "id": "location_id"},
        "additional_locations_id": {
            "label": "Additional Locations id",
            "id": "additional_locations_id",
        },
        "sftp_host": {"label": "SFTP host"},
        "sftp_port": {"label": "SFTP port"},
        "sftp_username": {"label": "SFTP username"},
        "sftp_password": {"label": "SFTP password"},
        "sftp_folder_path": {"label": "SFTP folder path"},
        "additional_sftp_folder_paths": {"label": "Additional locations folder paths"},
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

        # Put only available for user companies and locations in the select field
        form.company.query_factory = self._available_companies

        if current_user.permission == UserPermissionLevel.GLOBAL and form.company.data:
            form.location.query = Location.query.filter_by(
                company_id=form.company.data.id
            ).all()
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and form.company.data
            and form.location.data
        ):
            form.additional_locations.query = (
                Location.query.filter(
                    (Location.company_id == form.company.data.id)
                    & (Location.id != form.location.data.id)
                )
            ).all()
        else:
            form.location.query_factory = self._available_locations
            form.additional_locations.query_factory = self._available_locations

        return form

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """
        # Check that selected company is activated
        if form.company.data and form.activated.data:
            company = Company.query.filter_by(id=form.company.data.id).first()

            if not company.activated:
                flash(
                    gettext(
                        "Failed to create record. Selected company is not activated."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Selected company is not activated."
                )

                return False

        # Check that selected location is active and has appropriate amount of activated computers
        if form.activated.data and form.location.data:
            location = Location.query.filter_by(id=form.location.data.id).first()
            location_activated_computers = Computer.query.filter_by(
                location_id=location.id, activated=True
            ).count()

            if not location:
                flash(
                    gettext("Failed to create record. Location doesn't exist."),
                    "error",
                )
                logger.error(
                    "Failed to create record. Selected location doesn't exist."
                )

                return False

            if not location.activated:
                flash(
                    gettext(
                        "Failed to create record. Selected location is not activated."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Selected location is not activated."
                )

                return False

            if (
                location.company.is_trial
                and location_activated_computers
                > CFG.MAX_LOCATION_ACTIVE_COMPUTERS_LITE
            ):
                flash(
                    gettext(
                        "Could not activate the new computer.\
                        Limit of 1 computer per location while using eMAR Vault Lite edition.\
                        Contact sales@emarvault.com to upgrade!"
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Locations of the trial company can have only one computer."
                )

                return False
            elif (
                not location.company.is_trial
                and location_activated_computers
                >= CFG.MAX_LOCATION_ACTIVE_COMPUTERS_PRO
            ):
                flash(
                    gettext(
                        "Could not activate the new computer. \
                        Limit of 5 computers per location while using eMAR Vault Pro edition."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to create record. Locations can have only 5 computers."
                )

                return False

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

                if form.activated.data:
                    model.deactivated_at = None
                else:
                    model.deactivated_at = datetime.utcnow()

                if form.logs_enabled.data:
                    model.last_time_logs_enabled = datetime.utcnow()

                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info("Computer {} was restored.", model.computer_name)
            else:
                model = self.build_new_instance()

                form.populate_obj(model)

                if not form.activated.data:
                    model.deactivated_at = datetime.utcnow()

                if not form.logs_enabled.data:
                    model.last_time_logs_enabled = None
                    model.last_time_logs_disabled = datetime.utcnow()

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
        # Check that selected company is activated
        if form.company.data and form.activated.data:
            company = Company.query.filter_by(id=form.company.data.id).first()

            if not company.activated:
                flash(
                    gettext(
                        "Failed to update record. Selected company is not activated."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Selected company is not activated."
                )

                return False

        # Check that selected location has appropriate amount of active computers
        if form.activated.data and form.location.data:
            location = Location.query.filter_by(id=form.location.data.id).first()
            location_activated_computers = Computer.query.filter_by(
                location_id=location.id, activated=True
            ).count()

            if not location:
                flash(
                    gettext("Failed to update record. Location doesn't exist."),
                    "error",
                )
                logger.error("Failed to update record. Location doesn't exist.")

                return False

            if not location.activated:
                flash(
                    gettext(
                        "Failed to update record. Selected location is not activated."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Selected location is not activated."
                )

                return False

            if (
                location.company.is_trial
                and location_activated_computers
                > CFG.MAX_LOCATION_ACTIVE_COMPUTERS_LITE
            ):
                flash(
                    gettext(
                        "Could not activate the new computer.\
                        Limit of 1 computer per location while using eMAR Vault Lite edition.\
                        Contact sales@emarvault.com to upgrade!"
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Locations of the trial company can have only one computer."
                )

                return False
            elif (
                not location.company.is_trial
                and location_activated_computers
                >= CFG.MAX_LOCATION_ACTIVE_COMPUTERS_PRO
            ):
                flash(
                    gettext(
                        "Could not activate the new computer. \
                        Limit of 5 computers per location while using eMAR Vault Pro edition."
                    ),
                    "error",
                )
                logger.error(
                    "Failed to update record. Locations can have only 5 computers."
                )

                return False

        # check if there was additional_locations added
        if form.additional_locations.data:
            for location in form.additional_locations.data:
                location = Location.query.filter_by(id=location.id).first()
                location_activated_computers = Computer.query.filter_by(
                    location_id=location.id, activated=True
                ).count()

                if not location:
                    flash(
                        gettext("Failed to update record. Location doesn't exist."),
                        "error",
                    )
                    logger.error("Failed to update record. Location doesn't exist.")

                    return False

                if not location.activated:
                    flash(
                        gettext(
                            "Failed to update record. Selected location is not activated."
                        ),
                        "error",
                    )
                    logger.error(
                        "Failed to update record. Selected location is not activated."
                    )

                    return False

                if (
                    location.company.is_trial
                    and location_activated_computers
                    > CFG.MAX_LOCATION_ACTIVE_COMPUTERS_LITE
                ):
                    flash(
                        gettext(
                            "Could not activate the new computer.\
                            Limit of 1 computer per location while using eMAR Vault Lite edition.\
                            Contact sales@emarvault.com to upgrade!"
                        ),
                        "error",
                    )
                    logger.error(
                        "Failed to update record. Locations of the trial company can have only one computer."
                    )

                    return False
                elif (
                    not location.company.is_trial
                    and location_activated_computers
                    >= CFG.MAX_LOCATION_ACTIVE_COMPUTERS_PRO
                ):
                    flash(
                        gettext(
                            "Could not activate the new computer. \
                            Limit of 5 computers per location while using eMAR Vault Pro edition."
                        ),
                        "error",
                    )
                    logger.error(
                        "Failed to update record. Locations can have only 5 computers."
                    )

                    return False

        try:
            model_copy = copy(model)
            additional_locations_data = form.additional_locations.data
            additional_locations_copy = list(model.additional_locations)
            delattr(form, "additional_locations")
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            if additional_locations_data or additional_locations_data == []:
                for loc in additional_locations_copy:
                    model.additional_locations.remove(loc)
                    db.session.delete(loc)
                    db.session.commit()
                for location in additional_locations_data:
                    loc = AdditionalLocation(
                        location_id=location.id, computer_id=model.id
                    ).save()
                    logger.info(
                        f"Additional location {loc.location_id} added to computer {model.computer_name}"
                    )
            if form.logs_enabled.data != model_copy.logs_enabled:
                if form.logs_enabled.data:
                    model.last_time_logs_enabled = datetime.utcnow()
                else:
                    model.last_time_logs_disabled = datetime.utcnow()

            if form.activated.data != model_copy.activated:
                if form.activated.data:
                    model.activate(commit=False)
                else:
                    model.deactivate(commit=False)

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
        else:
            if "delete" not in self.action_disallowed_list:
                self.action_disallowed_list.append("delete")

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

    def get_one(self, id):
        return self.model.query.filter_by(id=tools.iterdecode(id)).first()
