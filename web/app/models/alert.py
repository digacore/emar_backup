from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from sqlalchemy import func

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView
from .system_log import SystemLogType
from .user import UserPermissionLevel, UserRole

from app.logger import logger


class Alert(db.Model, ModelMixin):

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(64), unique=True, nullable=False)
    from_email = db.Column(db.String(128))
    to_addresses = db.Column(db.String(128))
    subject = db.Column(db.String(128))
    body = db.Column(db.String(512))
    html_body = db.Column(db.String(512))
    alert_status = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "from_email",
            "to_addresses",
            "subject",
            "body",
            "html_body",
            "alert_status",
        ]


class AlertView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "AlertView"

    column_list = [
        "name",
        "from_email",
        "to_addresses",
        "subject",
        "body",
        "html_body",
        "alert_status",
    ]

    column_searchable_list = ["name", "from_email", "to_addresses"]

    column_filters = column_list

    action_disallowed_list = ["delete"]

    def _can_edit(self, model):
        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
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

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that alert was created or updated
        if is_created:
            create_system_log(SystemLogType.ALERT_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.ALERT_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that alert was deleted
        create_system_log(SystemLogType.ALERT_DELETED, model, current_user)

    # list rows depending on current user permissions
    def get_query(self):

        logger.debug(
            "alert.py get_query() current_user={}, permission={}, role={}",
            current_user,
            current_user.permission.value,
            current_user.role.value,
        )

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
            case _:
                result_query = self.session.query(self.model).filter(
                    self.model.id == -1
                )

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        if current_user.permission == UserPermissionLevel.GLOBAL:
            return actual_query.with_entities(func.count()).select_from(self.model)

        return actual_query.with_entities(func.count())
