from datetime import datetime

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from .computer import Computer
from .location import Location


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
        ]


class CompanyView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "CompanyView"

    column_list = [
        "name",
        "default_sftp_username",
        "locations_per_company",
        "total_computers",
        "computers_online",
        "computers_offline",
    ]
    column_filters = column_list

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

    def get_query(self):

        # NOTE Update number of Locations and Computers in Companies
        computers = Computer.query.all()
        locations = Location.query.all()
        companies = Company.query.all()

        if companies:
            computer_company = [co.company_name for co in computers]
            location_company = [loc.company_name for loc in locations]
            for company in companies:
                company.total_computers = computer_company.count(company.name)
                # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
                computers_online_per_company = [
                    comp.alert_status for comp in computers if comp.company == company
                ]
                computers_online = computers_online_per_company.count("green")
                company.computers_online = computers_online
                company.computers_offline = (
                    len(computers_online_per_company) - computers_online
                )
                company.locations_per_company = location_company.count(company.name)
                company.update()

        # NOTE handle permissions - meaning which details current user could view
        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False

            user_permission: str = current_user.asociated_with
            if (
                user_permission.lower() == "global-full"
                or user_permission.lower() == "global-view"
            ):
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(
                    self.model.name == user_permission
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.computer_name == "None"
            )
        return result_query
