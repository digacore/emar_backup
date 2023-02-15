from datetime import datetime

# from sqlalchemy import or_
# from sqlalchemy.orm import relationship

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.controllers import MyModelView

from .user import UserView


class Alert(db.Model, ModelMixin):

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    from_email = db.Column(db.String(128))
    to_addresses = db.Column(db.String(128))
    subject = db.Column(db.String(128))
    body = db.Column(db.String(512))
    html_body = db.Column(db.String(512))
    # alerted_target = db.Column(db.String(128))
    alert_status = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class AlertView(RowActionListMixin, MyModelView):
    column_hide_backrefs = False
    # column_list = ["id", "name", "company_name", "created_at"]
    column_searchable_list = ["name", "from_email", "to_addresses"]
    form_widget_args = {
        "name": {"readonly": True},
    }

    def edit_form(self, obj):
        form = super(AlertView, self).edit_form(obj)

        query_res = self.session.query(Alert).all()

        permissions = [i[0] for i in UserView.form_choices['asociated_with']]
        for location in [i.name for i in query_res]:
            if location in permissions:
                break
            print(f"{location} added")
            UserView.form_choices['asociated_with'].append((location, f"Location-{location}"))
        print(f"permissions updated {permissions}")

        form.name.query = query_res
        return form

    def _can_edit(self, model):
        # return True to allow edit
        return True
        # print("current_user", current_user.username, current_user.asociated_with)
        # if current_user.asociated_with == "global-full":
        #     return True
        # else:
        #     return False

    def _can_delete(self, model):
        print("current_user", current_user.username, current_user.asociated_with)
        if current_user.asociated_with == "global-full":
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
        print("location get_query current_user", current_user, current_user.asociated_with)
        if current_user:
            user_permission: str = current_user.asociated_with
            if user_permission.lower() == "global-full":
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(self.model.computer_name == "None")
        else:
            result_query = self.session.query(self.model).filter(self.model.computer_name == "None")
        return result_query
