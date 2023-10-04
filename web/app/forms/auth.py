from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
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
