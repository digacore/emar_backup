from datetime import datetime

from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.forms import LoginForm

from config import BaseConfig as CFG


auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user: User = User.authenticate(form.user_id.data, form.password.data)
        if user is not None:
            if user.activated:
                user.last_time_online = CFG.offset_to_est(
                    datetime.now().replace(microsecond=0), True
                )
                user.update()
                login_user(user)
                flash("Login successful.", "success")
                return redirect(url_for("main.index"))

            flash("This user is deactivated", "danger")
            return render_template("auth/login.html", form=form)

        flash("Wrong user ID or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_blueprint.route("/logout")
@login_required
def logout():
    current_user.last_time_online = CFG.offset_to_est(
        datetime.now().replace(microsecond=0), True
    )
    current_user.update()
    logout_user()
    flash("You were logged out.", "info")
    return redirect(url_for("main.index"))
