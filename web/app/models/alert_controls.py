from datetime import datetime

from sqlalchemy.orm import relationship
from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView


class AlertControls(db.Model, ModelMixin):

    __tablename__ = "alert_controls"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    alert_period = db.Column(db.Integer)
    alert = relationship("Alert", passive_deletes=True, lazy="select")
    # TODO swap company name to company id. Same for all models
    alert_associated = db.Column(
        db.Integer, db.ForeignKey("alerts.id", ondelete="CASCADE")
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class AlertControlsView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "AlertControlsView"

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
