from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from sqlalchemy import func

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.models.user import UserPermissionLevel, UserRole
from app.utils import MyModelView


class ClientVersion(db.Model, ModelMixin):
    __tablename__ = "client_versions"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return self.name


class ClientVersionView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ClientVersionView"

    form_choices = {"name": [("stable", "stable"), ("latest", "latest")]}

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
        # NOTE deletes not allowed as only 2 options are available
        return False

    def allow_row_action(self, action, model):
        if isinstance(action, EditRowAction):
            return self._can_edit(model)

        if isinstance(action, DeleteRowAction):
            return self._can_delete(model)

        # otherwise whatever the inherited method returns
        return super().allow_row_action(action, model)

    # list rows depending on current user permissions
    def get_query(self):
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            self.can_create = True
        else:
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
