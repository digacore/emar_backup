from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView


class ClientVersion(db.Model, ModelMixin):

    __tablename__ = "client_versions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class ClientVersionView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ClientVersionView"

    list_template = "import-admin-list-to-dashboard.html"

    form_choices = {"name": [("stable", "stable"), ("latest", "latest")]}

    action_disallowed_list = ["delete"]

    def _can_edit(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
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

        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
                result_query = self.session.query(self.model)
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False
                result_query = self.session.query(self.model).filter(
                    self.model.name == "None"
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.name == "None"
            )
        return result_query
