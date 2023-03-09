from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from app.logger import logger


class Company(db.Model, ModelMixin):

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    locations_per_company = db.Column(db.Integer)
    total_computers = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "locations_per_company",
            "total_computers",
            "computers_online",
            "computers_offline",
        ]


class CompanyView(RowActionListMixin, MyModelView):

    list_template = 'import-admin-list-to-dashboard.html'

    column_list = [
        "name",
        "locations_per_company",
        "total_computers",
        "computers_online",
        "computers_offline",
    ]

    column_searchable_list = column_list

    action_disallowed_list = ["delete"]

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

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
        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False

        logger.debug(
            "company.py get_query() current_user={}, asociated_with={}",
            current_user,
            current_user.asociated_with
        )
        if current_user:
            user_permission: str = current_user.asociated_with
            if user_permission.lower() == "global-full" or user_permission.lower() == "global-view":
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(self.model.name == user_permission)
        else:
            result_query = self.session.query(self.model).filter(self.model.computer_name == "None")
        return result_query
