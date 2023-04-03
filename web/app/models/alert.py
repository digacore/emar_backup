from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

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
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        if str(current_user.asociated_with).lower() == "global-full":
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

    # list rows depending on current user permissions
    def get_query(self):

        logger.debug(
            "alert.py get_query() current_user={}, asociated_with={}",
            current_user,
            current_user.asociated_with,
        )
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
