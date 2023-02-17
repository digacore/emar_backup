from gettext import gettext

from werkzeug.datastructures import FileStorage
from wtforms.validators import InputRequired
from wtforms.widgets import FileInput
from wtforms import ValidationError, fields

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


class RowActionListMixin(object):

    list_template = 'admin/list.html'

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

        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in
                map(lambda x: x.lower(), self.allowed_extensions))

    def _is_uploaded_file(self, data):
        return (data and isinstance(data, FileStorage) and data.filename)

    def pre_validate(self, form):
        super(BlobUploadField, self).pre_validate(form)
        if self._is_uploaded_file(self.data) and not self.is_file_allowed(self.data.filename):
            raise ValidationError(gettext('Invalid file extension'))

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
