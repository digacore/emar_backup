from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from sqlalchemy import sql, func, and_, or_
from sqlalchemy.orm import Query, relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView
from .system_log import SystemLogType

from config import BaseConfig as CFG


class Company(db.Model, ModelMixin):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(64), unique=True, nullable=False)
    default_sftp_username = db.Column(db.String(128))
    default_sftp_password = db.Column(db.String(128))
    locations_per_company = db.Column(db.Integer)
    total_computers = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pcc_org_id = db.Column(db.String(128), nullable=True)
    created_from_pcc = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )
    is_global = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )

    computers = relationship(
        "Computer",
        back_populates="company",
        cascade="all, delete",
        passive_deletes=True,
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

    @hybrid_property
    def total_computers_counter(self):
        from app.models.computer import Computer

        computers_number: int = Computer.query.filter(
            Computer.company_id == self.id,
            Computer.activated.is_(True),
        ).count()
        return computers_number

    @hybrid_property
    def primary_computers_offline(self):
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
        from app.models.alert_event import AlertEvent

        # If the start_time and end_time has not UTC timezone, then convert it
        if start_time.tzinfo and start_time.tzinfo != ZoneInfo("UTC"):
            start_time = start_time.astimezone(ZoneInfo("UTC"))

        if end_time.tzinfo and end_time.tzinfo != ZoneInfo("UTC"):
            end_time = end_time.astimezone(ZoneInfo("UTC"))

        location_ids: list[int] = [location.id for location in self.locations]
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

    form_widget_args = {
        "locations_per_company": {"readonly": True},
        "total_computers": {"readonly": True},
        "computers_online": {"readonly": True},
        "computers_offline": {"readonly": True},
        "created_at": {"readonly": True},
    }

    # To set order of the fields in form
    form_columns = (
        "name",
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
    )

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
                result_query = self.session.query(self.model)
            case UserPermissionLevel.COMPANY:
                result_query = self.session.query(self.model).filter(
                    self.model.id == current_user.company_id
                )
            case _:
                result_query = self.session.query(self.model).filter(
                    self.model.id == -1
                )

        return result_query.filter(self.model.is_global.is_(False))

    def get_count_query(self):
        actual_query = self.get_query()
        return actual_query.with_entities(func.count())
