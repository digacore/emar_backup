from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from sqlalchemy import select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app import db, models as m
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView


# The location column is unique to prevent situation when location is connected to several groups
locations_to_group = db.Table(
    "locations_to_groups",
    db.metadata,
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

    locations = relationship("Location", secondary=locations_to_group, backref="group")

    def __repr__(self):
        return self.name

    @hybrid_property
    def company_name(self):
        return self.company.name

    @company_name.expression
    def company_name(cls):
        return (
            select([m.Company.name]).where(cls.company_id == m.Company.id).as_scalar()
        )


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
