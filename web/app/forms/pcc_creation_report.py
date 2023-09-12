from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class CreationReportForm(FlaskForm):
    data = StringField("Creation report JSON data", [DataRequired()])
