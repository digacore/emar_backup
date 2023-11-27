from datetime import datetime, timedelta

from flask import flash
from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from flask_admin.contrib.sqla import tools
from flask_admin.babel import gettext
from sqlalchemy import select, func, and_, or_, sql
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from .company import Company
from .location import Location
from .utils import ModelMixin, RowActionListMixin, SoftDeleteMixin, QueryWithSoftDelete
from app.utils import MyModelView
from app.logger import logger

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


class LocationGroup(db.Model, ModelMixin, SoftDeleteMixin):
    __tablename__ = "location_groups"

    __table_args__ = (db.UniqueConstraint("company_id", "name"),)

    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, server_default=db.func.now()
    )
    # Redefine is_deleted column from SoftDeleteMixin to be able to use it in relation
    is_deleted = db.Column(db.Boolean, default=False, server_default=sql.false())

    company = relationship(
        "Company",
        back_populates="location_groups",
    )

    locations = relationship(
        "Location",
        secondary=locations_to_group,
        primaryjoin=and_(
            id == locations_to_group.c.location_group_id, is_deleted.is_(False)
        ),
        secondaryjoin=and_(
            locations_to_group.c.location_id == Location.id,
            Location.is_deleted.is_(False),
        ),
        backref="group",
    )

    def __repr__(self):
        return self.name

    def delete(self, commit: bool = True):
        """Soft delete location group

        Args:
            commit (bool, optional): Commit changes. Defaults to True.
        """
        # Delete location group users
        for user in self.users:
            user.delete(commit=False)

        # Delete all locations from group
        self.locations = []

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

        if commit:
            db.session.commit()
        return self

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
                    < current_east_time - timedelta(hours=1, minutes=30),
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
                    < current_east_time - timedelta(hours=1, minutes=30),
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
                Computer.last_download_time
                >= current_east_time - timedelta(hours=1, minutes=30),
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

    form_excluded_columns = ["users", "created_at", "deleted_at", "is_deleted"]

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

    def create_model(self, form):
        """
        Create model from form.

        :param form:
            Form instance
        """

        # Check if there is deleted location group with such name and for such company
        deleted_group = (
            LocationGroup.query.with_deleted()
            .filter_by(
                name=form.name.data,
                company_id=form.company.data.id,
                is_deleted=True,
            )
            .first()
        )

        try:
            if deleted_group:
                # Restore group
                model = deleted_group
                original_created_at = model.created_at
                form.populate_obj(model)
                model.is_deleted = False
                model.deleted_at = None
                model.created_at = original_created_at
                self._on_model_change(form, model, True)
                self.session.commit()

                logger.info(f"Location group {model.name} was restored.")
            else:
                model = self.build_new_instance()

                form.populate_obj(model)
                self.session.add(model)
                self._on_model_change(form, model, True)
                self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to create record. %(error)s", error=str(ex)),
                    "error",
                )
                logger.error("Failed to create record.")

            self.session.rollback()

            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def delete_model(self, model):
        """
        Soft deletion of model

        :param model:
            Model to delete
        """
        try:
            self.on_model_delete(model)
            self.session.flush()

            model.delete(commit=False)

            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(
                    gettext("Failed to delete record. %(error)s", error=str(ex)),
                    "error",
                )
                logger.error("Failed to delete record.")

            self.session.rollback()

            return False
        else:
            self.after_model_delete(model)

        return True

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
                result_query = self.model.query
            case UserPermissionLevel.COMPANY:
                result_query = self.model.query.filter(
                    self.model.company_id == current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                result_query = self.model.query.filter(
                    self.model.id == current_user.location_group[0].id
                )
            case _:
                result_query = self.model.query.filter(self.model.id == -1)

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        return actual_query.with_entities(func.count())

    def get_one(self, id):
        return self.model.query.filter_by(id=tools.iterdecode(id)).first()
