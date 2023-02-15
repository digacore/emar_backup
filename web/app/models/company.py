from datetime import datetime

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.controllers import MyModelView

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from .user import UserView


class Company(db.Model, ModelMixin):

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class CompanyView(RowActionListMixin, MyModelView):

    def edit_form(self, obj):
        form = super(CompanyView, self).edit_form(obj)

        query_res = self.session.query(Company).all()

        permissions = [i[0] for i in UserView.form_choices['asociated_with']]
        for company in [i.name for i in query_res]:
            if company in permissions:
                break
            print(f"{company} added")
            UserView.form_choices['asociated_with'].append((company, f"Company-{company}"))
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
        print("company get_query current_user", current_user, current_user.asociated_with)
        if current_user:
            user_permission: str = current_user.asociated_with
            if user_permission.lower() == "global-full" or user_permission.lower() == "global-view":
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(self.model.name == user_permission)
        else:
            result_query = self.session.query(self.model).filter(self.model.computer_name == "None")
        return result_query
