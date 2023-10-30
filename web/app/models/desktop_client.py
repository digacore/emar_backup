from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction
from markupsafe import Markup

from app import db

from app.models.client_version import ClientVersion
from app.models.user import UserPermissionLevel, UserRole
from app.models.utils import ModelMixin, RowActionListMixin, BlobMixin, BlobUploadField
from app.utils import MyModelView


class DesktopClient(db.Model, ModelMixin, BlobMixin):

    __tablename__ = "desktop_clients"

    id = db.Column(db.Integer, primary_key=True)

    flag_id = db.Column(
        db.Integer,
        db.ForeignKey("client_versions.id", ondelete="CASCADE"),
        nullable=True,
    )

    name = db.Column(db.String(64), unique=True, nullable=False)
    version = db.Column(db.String(64))
    description = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.now)

    flag = relationship("ClientVersion", passive_deletes=True)

    def __repr__(self):
        return self.name

    def __unicode__(self):
        return "name : {name}; filename : {filename})".format(
            name=self.name, filename=self.filename
        )

    @hybrid_property
    def flag_name(self):
        return self.flag.name if self.flag else None

    @flag_name.expression
    def flag_name(cls):
        return (
            select([ClientVersion.name])
            .where(cls.flag_id == ClientVersion.id)
            .as_scalar()
        )

    @flag_name.setter
    def flag_name(self, value):
        new_flag = ClientVersion.query.filter_by(name=value).first()
        self.flag_id = new_flag.id if new_flag else None


class DesktopClientView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "DesktopClientView"

    column_searchable_list = ["name", "version", "flag_name"]

    column_list = (
        "name",
        "version",
        "flag_name",
        "description",
        "filename",
        "download",
    )
    form_excluded_columns = ("mimetype", "size", "filename")

    form_extra_fields = {
        "blob": BlobUploadField(
            label="File",
            allowed_extensions=["msi"],
            size_field="size",
            filename_field="filename",
            mimetype_field="mimetype",
        )
    }

    column_filters = (
        "name",
        "version",
        "flag_name",
        "description",
        "filename",
    )
    action_disallowed_list = ["delete"]
    column_default_sort = ("version", True)

    def _download_formatter(self, context, model, name):
        return Markup(
            "<a href='{url}' target='_blank'>Download</a>".format(
                url=self.get_url("download_msi.download_msi", id=model.id)
            )
        )

    column_formatters = {
        "download": _download_formatter,
    }

    def _can_edit(self, model):
        # return True to allow edit
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            return True
        else:
            return False

    def _can_delete(self, model):
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

    # list rows depending on current user permissions
    def get_query(self):

        # check permissions
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

        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            result_query = self.session.query(self.model)
        elif current_user.role == UserRole.ADMIN:
            result_query = self.session.query(self.model).filter(
                self.model.flag_id.is_not(None)
            )
        else:
            result_query = self.session.query(self.model).filter(self.model.id == -1)

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            return actual_query.with_entities(func.count()).select_from(self.model)

        return actual_query.with_entities(func.count())
