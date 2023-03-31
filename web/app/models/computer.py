from datetime import datetime

from sqlalchemy import JSON, or_
from sqlalchemy.orm import relationship

from flask_admin.model.template import EditRowAction, DeleteRowAction

from flask_login import current_user

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from .location import Location
from .company import Company
from .desktop_client import DesktopClient

from config import BaseConfig as CFG


# TODO add to all models secure form? csrf
# from flask_admin.form import SecureForm
# from flask_admin.contrib.sqla import ModelView

# class CarAdmin(ModelView):
#     form_base_class = SecureForm


class Computer(db.Model, ModelMixin):

    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)
    computer_name = db.Column(db.String(64), unique=True, nullable=False)

    company = relationship(
        "Company", passive_deletes=True, backref="computers", lazy="select"
    )
    company_name = db.Column(
        db.String, db.ForeignKey("companies.name", ondelete="CASCADE")
    )
    location = relationship(
        "Location", passive_deletes=True, backref="computers", lazy="select"
    )
    location_name = db.Column(
        db.String, db.ForeignKey("locations.name", ondelete="CASCADE")
    )

    sftp_host = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_HOST)
    sftp_username = db.Column(db.String(64), default=CFG.DEFAULT_SFTP_USERNAME)
    sftp_password = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_PASSWORD)
    sftp_folder_path = db.Column(db.String(256))
    folder_password = db.Column(db.String(128), default=CFG.DEFAULT_FOLDER_PASSWORD)

    type = db.Column(db.String(128))
    msi_version = db.Column(db.String(64))
    current_msi_version = db.Column(db.String(64))

    alert_status = db.Column(db.String(128))
    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="new_computer", nullable=False)

    manager_host = db.Column(db.String(256))
    last_downloaded = db.Column(db.String(256))
    files_checksum = db.Column(JSON)
    # TODO do we need this one? Could computer be deactivated?
    activated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.computer_name

    def _cols(self):
        return [
            "computer_name",
            "alert_status",
            "company_name",
            "location_name",
            "download_status",
            "last_download_time",
            "last_time_online",
            "msi_version",
            "current_msi_version",
            "sftp_host",
            "sftp_username",
            "sftp_folder_path",
            "type",
            "manager_host",
            "activated",
            "files_checksum",
            "identifier_key",
        ]


class ComputerView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ComputerView"

    list_template = "import-computer-to-dashboard.html"

    # NOTE could be useful when define the permissions
    # can_create = False
    # can_edit = False
    # can_delete = False

    column_hide_backrefs = False
    column_list = [
        "computer_name",
        "alert_status",
        "company_name",
        "location_name",
        "download_status",
        "last_download_time",
        "last_time_online",
        "msi_version",
        "current_msi_version",
        "sftp_host",
        "sftp_username",
        "sftp_folder_path",
        "type",
        "manager_host",
        "activated",
    ]

    column_searchable_list = column_list
    column_sortable_list = column_list
    column_filters = column_list

    # NOTE allows edit in list view, but has troubles with permissions
    # column_editable_list = [
    #     # "computer_name",
    #     "company",
    #     # "location",
    #     # "type",
    #     # "sftp_host",
    #     # "sftp_username",
    #     # "sftp_folder_path",
    #     # "manager_host",
    # ]

    # TODO uncomment files_checksum when ready to go on
    form_widget_args = {
        "last_download_time": {"readonly": True},
        "last_time_online": {"readonly": True},
        "identifier_key": {"readonly": True},
        "created_at": {"readonly": True},
        "alert_status": {"readonly": True},
        "download_status": {"readonly": True},
        "last_downloaded": {"readonly": True},
        # "files_checksum": {"readonly": True},
    }

    # Added to control fields order. It is dict though...
    form_args = {
        "computer_name": {"label": "Computer name"},
        "company_name": {"label": "Company name", "id": "company_name"},
        "location_name": {"label": "Location name", "id": "location_name"},
        "sftp_host": {"label": "SFTP host"},
        "sftp_username": {"label": "SFTP username"},
        "sftp_password": {"label": "SFTP password"},
        "sftp_folder_path": {"label": "SFTP folder path"},
        "type": {"label": "Type"},
        "msi_version": {"label": "Msi version"},
        "current_msi_version": {"label": "Current msi version"},
        "manager_host": {"label": "Manager host"},
        "activated": {"label": "Activated"},
        "alert_status": {"label": "Alert status"},
        "download_status": {"label": "Download status"},
        "last_download_time": {"label": "Last download time"},
        "last_time_online": {"label": "Last time online"},
        "identifier_key": {"label": "Identifier key"},
        "files_checksum": {"label": "Files checksum"},
        "created_at": {"label": "Created at"},
    }

    form_choices = {"msi_version": CFG.CLIENT_VERSIONS}

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

        OBLIGATORY_VERSIONS = [
            ("stable", "stable"),
            ("latest", "latest"),
        ]

        versions = [i.version for i in DesktopClient.query.all()]

        # remove old versions from global versions variable
        for version in CFG.CLIENT_VERSIONS:
            if version[0] not in versions or version not in OBLIGATORY_VERSIONS:
                CFG.CLIENT_VERSIONS.remove(version)

        # add new versions to global versions variable
        for version in versions:
            if (version, version) not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append((version, version))
        for dversion in OBLIGATORY_VERSIONS:
            if dversion not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append(dversion)

        # TODO should we move this code to Location and Company??
        # NOTE Update Location and Company computers info
        computers = Computer.query.all()
        computer_location = [loc.location_name for loc in computers]
        computer_company = [co.company_name for co in computers]

        # update number of computers in locations
        locations = Location.query.all()
        location_company = [loc.company_name for loc in locations]
        if locations:
            for location in locations:
                location.computers_per_location = computer_location.count(location.name)
                # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
                computers_online_per_location = [
                    comp.alert_status for comp in computers if comp.location == location
                ]
                computers_online = computers_online_per_location.count("green")
                location.computers_online = computers_online
                location.computers_offline = (
                    len(computers_online_per_location) - computers_online
                )
                location.update()

        # update number of locations and computers in companies
        companies = Company.query.all()
        if companies:
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

        # NOTE Check permissions
        self.form_choices = CFG.CLIENT_VERSIONS

        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False

        if current_user:
            user_permission: str = current_user.asociated_with
            if (
                user_permission.lower() == "global-full"
                or user_permission.lower() == "global-view"
            ):
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(
                    or_(
                        self.model.location_name == user_permission,
                        self.model.company_name == user_permission,
                    )
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.computer_name == "None"
            )
        return result_query
