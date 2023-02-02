from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

from config import BaseConfig as BCG


class EmailForm(FlaskForm):
    # array or dict with array values
    templates = {
        "temp_1": ["subject 1", "body 1"],
        "temp_2": ["subject 2", "body 2"],
        }
    template = SelectField('Choose email template', choices=templates)
    from_email = StringField('From email', validators=[Email()], default=BCG.SUPPORT_EMAIL)
    to_addresses = StringField('To addresses', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(0, 100)], default="subject")
    body = TextAreaField('Body', validators=[DataRequired()], default="body")
    html_body = TextAreaField('HTML body')
    # reply_to_address = StringField('Reply to address', validators=[Email()])
    # reply_to_address = StringField('Reply to address')
    submit = SubmitField('Send Email')
