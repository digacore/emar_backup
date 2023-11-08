from datetime import datetime, timedelta

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from .company import Company
from .location import Location
from .utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from config import BaseConfig as CFG


# The location column is unique to prevent situation when location is connected to several groups
locations_to_group = db.Table(
    "locations_to_groups",
    db.metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column(
        "location_id",
        db.Integer,
        db.ForeignKey("locations.id"),
        unique=True,
        nullable=False,
    ),
    db.Column(
        "location_group_id",
        db.Integer,
        db.ForeignKey("location_groups.id"),
        nullable=False,
    ),
)


class LocationGroup(db.Model, ModelMixin):
    __tablename__ = "location_groups"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    name = db.Column(db.String(64), nullable=False)

    company = relationship(
        "Company",
        passive_deletes=True,
    )

    locations = relationship(
        "Location",
        secondary=locations_to_group,
        secondaryjoin=and_(
            locations_to_group.c.location_id == Location.id,
            Location.is_deleted.is_(False),
        ),
        backref="group",
    )

    def __repr__(self):
        return self.name

    @hybrid_property
    def company_name(self):
        return self.company.name

    @company_name.expression
    def company_name(cls):
        return select([Company.name]).where(cls.company_id == Company.id).as_scalar()

    @hybrid_property
    def total_computers(self):
        from app.models.computer import Computer

        location_ids: list[int] = [location.id for location in self.locations]

        computers_number: int = Computer.query.filter(
            Computer.location_id.in_(location_ids),
            Computer.activated.is_(True),
        ).count()
        return computers_number

    @hybrid_property
    def primary_computers_offline(self):
        from app.models.computer import Computer, DeviceRole

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)

        location_ids: list[int] = [location.id for location in self.locations]

        computers_number = Computer.query.filter(
            and_(
                Computer.location_id.in_(location_ids),
                Computer.activated.is_(True),
                Computer.device_role == DeviceRole.PRIMARY,
                or_(
                    Computer.last_download_time.is_(None),
                    Computer.last_download_time
                    < current_east_time - timedelta(hours=1),
                ),
            )
        ).count()

        return computers_number

    @hybrid_property
    def total_offline_computers(self):
        from app.models.computer import Computer

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)

        location_ids: list[int] = [location.id for location in self.locations]

        computers_number = Computer.query.filter(
            and_(
                Computer.location_id.in_(location_ids),
                Computer.activated.is_(True),
                or_(
                    Computer.last_download_time.is_(None),
                    Computer.last_download_time
                    < current_east_time - timedelta(hours=1),
                ),
            )
        ).count()

        return computers_number

    @hybrid_property
    def total_offline_locations(self):
        from app.models.computer import Computer

        current_east_time = CFG.offset_to_est(datetime.utcnow(), True)
        offline_locations_counter = 0

        locations = self.locations

        for location in locations:
            activated_computers_query = Computer.query.filter(
                Computer.location_id == location.id,
                Computer.activated.is_(True),
            )

            if not activated_computers_query.count():
                continue

            online_computers = activated_computers_query.filter(
                Computer.last_download_time.is_not(None),
                Computer.last_download_time >= current_east_time - timedelta(hours=1),
            ).all()

            if not online_computers:
                offline_locations_counter += 1

        return offline_locations_counter


class LocationGroupView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "LocationGroupView"

    create_template = "location-groups-create.html"
    edit_template = "location-groups-edit.html"

    column_hide_backrefs = False
    column_list = ["name", "company_name"]

    column_searchable_list = column_list
    column_filters = column_list
    column_sortable_list = column_list
    action_disallowed_list = ["delete"]

    form_excluded_columns = ["users"]

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def _can_edit(self, model):
        from app.models.user import UserPermissionLevel, UserRole

        if (
            current_user.permission.value
            in [UserPermissionLevel.GLOBAL.value, UserPermissionLevel.COMPANY.value]
            and current_user.role == UserRole.ADMIN
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
        from app.models.user import UserPermissionLevel, UserRole

        if (
            current_user.permission.value
            in [UserPermissionLevel.GLOBAL.value, UserPermissionLevel.COMPANY.value]
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

    def create_form(self, obj=None):
        form = super().create_form(obj)

        form.company.query_factory = self._available_companies

        locations_query = self._available_locations()
        # Filter locations which are already in group
        final_query = locations_query.filter(~Location.group.any())
        form.locations.query_factory = lambda: final_query

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        form.company.query_factory = self._available_companies
        form.locations.query_factory = self._available_locations

        return form

    def get_query(self):
        from app.models.user import UserPermissionLevel, UserRole

        # NOTE handle permissions - meaning which details current user could view
        if (
            current_user.permission.value
            in [UserPermissionLevel.GLOBAL.value, UserPermissionLevel.COMPANY.value]
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
                result_query = self.session.query(self.model).filter(
                    self.model.id == current_user.location_group[0].id
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
