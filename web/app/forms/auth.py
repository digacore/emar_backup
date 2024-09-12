from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, EqualTo


class LoginForm(FlaskForm):
    user_id = StringField("Username or Email", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Login")


class ChangePasswordForm(FlaskForm):
    user_id = IntegerField("User ID", [DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            EqualTo(
                "confirm_new_password", message="Password confirmation doesn't match."
            ),
        ],
    )
    confirm_new_password = PasswordField("Confirm New Password", [DataRequired()])


class ChangeNotificationSettings(FlaskForm):
    user_id = IntegerField("User ID", [DataRequired()])
    user_email = StringField("Email", [DataRequired()])
    receive_alert_emails = BooleanField("receive_alert_emails")
    receive_summaries_emails = BooleanField("receive_summaries_emails")
    receive_device_test_emails = BooleanField("receive_device_test_emails")
    submit = SubmitField("Update")
