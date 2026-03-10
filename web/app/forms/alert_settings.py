from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField


class AlertSettingsForm(FlaskForm):
    support_emails = TextAreaField("Support emails")
    submit = SubmitField("Save")
