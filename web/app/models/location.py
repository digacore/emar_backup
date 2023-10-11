from datetime import datetime

from sqlalchemy import func, sql, select
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from flask_admin.form import Select2Widget
from flask_admin.contrib.sqla.fields import QuerySelectField

from wtforms import validators

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView
from .company import Company
from .system_log import SystemLogType


class Location(db.Model, ModelMixin):

    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    name = db.Column(db.String(64), nullable=False)
    default_sftp_path = db.Column(db.String(256))
    computers_per_location = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pcc_fac_id = db.Column(db.Integer, nullable=True)
    use_pcc_backup = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )
    created_from_pcc = db.Column(
        db.Boolean, default=False, server_default=sql.false(), nullable=False
    )

    company = relationship(
        "Company",
        passive_deletes=True,
        backref=backref("locations", cascade="delete"),
        lazy="select",
    )

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "company_id",
            "default_sftp_path",
            "computers_per_location",
            "computers_online",
            "computers_offline",
            "pcc_fac_id",
            "use_pcc_backup",
        ]

    @hybrid_property
    def company_name(self):
        return self.company.name if self.company else None

    @company_name.expression
    def company_name(cls):
        return select([Company.name]).where(cls.company_id == Company.id).as_scalar()

    @company_name.setter
    def company_name(self, value):
        new_company = Company.query.filter_by(name=value).first()
        self.company_id = new_company.id if new_company else None


class LocationView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "LocationView"

    list_template = "import-company_location-to-dashboard.html"

    column_hide_backrefs = False
    column_list = [
        "name",
        "company_name",
        "default_sftp_path",
        "computers_per_location",
        "computers_online",
        "computers_offline",
        "pcc_fac_id",
        "use_pcc_backup",
        "created_from_pcc",
    ]

    column_labels = dict(
        pcc_fac_id="PointClickCare Facility ID",
        use_pcc_backup="Use PointClickCare Backup",
        created_from_pcc="Created from PointClickCare",
    )

    column_searchable_list = column_list
    column_filters = column_list
    column_sortable_list = column_list
    action_disallowed_list = ["delete"]

    form_widget_args = {
        "computers_per_location": {"readonly": True},
        "total_computers": {"readonly": True},
        "computers_online": {"readonly": True},
        "computers_offline": {"readonly": True},
        "created_at": {"readonly": True},
    }

    form_excluded_columns = ("created_from_pcc", "users")

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def _can_edit(self, model):
        from app.models.user import UserPermissionLevel, UserRole

        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
        from app.models.user import UserPermissionLevel, UserRole

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

    # All these manipulations with group field are needed because
    # between Location and LocationGroup many-to-many relationship (Location can have only one group or no group)
    # But Flask-Admin builds form for many-to-many relationship as SelectMultipleField (we need SelectField)
    def get_create_form(self):
        form = super().get_create_form()
        form.group = QuerySelectField(
            "Group",
            validators=[validators.Optional()],
            allow_blank=True,
        )

        return form

    def create_form(self, obj=None):
        form = super().create_form(obj)

        form.company.query_factory = self._available_companies

        form.group.widget = Select2Widget()
        form.group.query_factory = self._available_location_groups

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        # apply a sort to the relation
        form.company.query_factory = self._available_companies
        form.group.query_factory = self._available_location_groups

        return form

    def create_model(self, form):
        group_data = form.group.data
        del form.group
        model = super().create_model(form)
        model.group = [group_data]
        self.session.add(model)
        self.session.commit()

        return model

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that location was created or updated
        if is_created:
            create_system_log(SystemLogType.LOCATION_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.LOCATION_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that location was deleted
        create_system_log(SystemLogType.LOCATION_DELETED, model, current_user)

    def get_query(self):
        from app.models.user import UserPermissionLevel, UserRole

        # NOTE handle permissions - meaning which details current user could view
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
            case UserPermissionLevel.COMPANY:
                result_query = self.session.query(self.model).filter(
                    self.model.company_id == current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                locations = current_user.location_group[0].locations
                result_query = self.session.query(self.model).filter(
                    self.model.id.in_([location.id for location in locations])
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.session.query(self.model).filter(
                    self.model.id == current_user.location[0].id
                )
            case _:
                result_query = self.session.query(self.model).filter(
                    self.model.id == -1
                )

        return result_query

    def get_count_query(self):
        from app.models.user import UserPermissionLevel

        actual_query = self.get_query()

        # .with_entities(func.count()) doesn't count correctly when there is no filtering was applied to query
        # Instead add select_from(self.model) to query to count correctly
        if current_user.permission == UserPermissionLevel.GLOBAL:
            return actual_query.with_entities(func.count()).select_from(self.model)

        return actual_query.with_entities(func.count())
