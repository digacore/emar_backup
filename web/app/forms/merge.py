from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class MergeSecondaryCompany(FlaskForm):
    secondary_company = StringField("Secondary company for merge", [DataRequired()])
