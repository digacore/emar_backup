from datetime import datetime

from gettext import gettext

from werkzeug.datastructures import FileStorage
from wtforms.validators import InputRequired
from wtforms.widgets import FileInput
from wtforms import ValidationError, fields
from flask_sqlalchemy import BaseQuery
import sqlalchemy as sa

from app import db


class ModelMixin(object):
    def save(self):
        # Save this model to the database.
        db.session.add(self)
        db.session.commit()
        return self

    def update(self):
        # Update this model to the database.
        db.session.commit()
        return self


class SoftDeleteMixin(object):
    is_deleted = db.Column(db.Boolean, default=False, server_default=sa.sql.false())
    deleted_at = db.Column(db.DateTime, nullable=True)

    def delete(self):
        # Soft delete this model from the database.
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        db.session.commit()
        return self


class QueryWithSoftDelete(BaseQuery):
    def __new__(cls, *args, **kwargs):
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        with_deleted = kwargs.pop("_with_deleted", False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            return obj.filter_by(is_deleted=False) if not with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        return self.__class__(
            db.class_mapper(self._entity_from_pre_ent_zero().class_),
            session=db.session(),
            _with_deleted=True,
        )


class RowActionListMixin:
    list_template = "import-admin-list-to-dashboard.html"
    edit_template = "import-admin-edit-to-dashboard.html"
    create_template = "import-admin-create-to-dashboard.html"

    def allow_row_action(self, action, model):
        return True


class BlobUploadField(fields.StringField):
    widget = FileInput()

    def __init__(
        self,
        label=None,
        allowed_extensions=None,
        size_field=None,
        filename_field=None,
        mimetype_field=None,
        **kwargs
    ):
        self.allowed_extensions = allowed_extensions
        self.size_field = size_field
        self.filename_field = filename_field
        self.mimetype_field = mimetype_field
        validators = [InputRequired()]

        super(BlobUploadField, self).__init__(label, validators, **kwargs)

    def is_file_allowed(self, filename):
        """
        Check if file extension is allowed.

        :param filename:
            File name to check
        """
        if not self.allowed_extensions:
            return True

        return "." in filename and filename.rsplit(".", 1)[1].lower() in map(
            lambda x: x.lower(), self.allowed_extensions
        )

    def _is_uploaded_file(self, data):
        return data and isinstance(data, FileStorage) and data.filename

    def pre_validate(self, form):
        super(BlobUploadField, self).pre_validate(form)
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(
            self.data.filename
        ):
            raise ValidationError(gettext("Invalid file extension"))

    def process_formdata(self, valuelist):
        if valuelist:
            data = valuelist[0]
            self.data = data

    def populate_obj(self, obj, name):
        if self._is_uploaded_file(self.data):
            _blob = self.data.read()

            setattr(obj, name, _blob)

            if self.size_field:
                setattr(obj, self.size_field, len(_blob))

            if self.filename_field:
                setattr(obj, self.filename_field, self.data.filename)

            if self.mimetype_field:
                setattr(obj, self.mimetype_field, self.data.content_type)


class BlobMixin(object):
    mimetype = db.Column(db.Unicode(length=255), nullable=False)
    filename = db.Column(db.Unicode(length=255), nullable=False)
    blob = db.Column(db.LargeBinary(), nullable=False)
    size = db.Column(db.Integer, nullable=False)


def count(query: sa.sql.selectable.Select) -> int:
    # Return count of query.
    return db.session.execute(
        sa.select(sa.func.count()).select_from(query.subquery())
    ).scalar_one()
