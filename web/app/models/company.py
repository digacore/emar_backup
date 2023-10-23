from datetime import datetime, timedelta

from sqlalchemy import sql, func, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property
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

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)

        computers_number = Computer.query.filter(
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

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)

        computers_number = Computer.query.filter(
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

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)
        offline_locations_counter = 0

        locations = self.locations

        for location in locations:
            activated_computers_query = Computer.query.filter(
                Computer.location_id == location.id,
                Computer.activated.is_(True),
            )

            if not activated_computers_query.count():
                continue

            online_computers = activated_computers_query.filter(
                Computer.last_download_time.is_not(None),
                Computer.last_download_time >= current_east_time - timedelta(hours=1),
            ).all()

            if not online_computers:
                offline_locations_counter += 1

        return offline_locations_counter


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

    form_excluded_columns = ("created_from_pcc", "locations", "is_global", "users")

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
