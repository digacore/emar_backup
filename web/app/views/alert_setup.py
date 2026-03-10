from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms.alert_settings import AlertSettingsForm
from app.models import AlertSettings
from app.models.user import UserPermissionLevel, UserRole

alert_setup_blueprint = Blueprint("alert_setup", __name__, url_prefix="/alert-setup")


@alert_setup_blueprint.route("/", methods=["GET", "POST"])
@login_required
def index():
    if (
        current_user.permission != UserPermissionLevel.GLOBAL
        or current_user.role != UserRole.ADMIN
    ):
        flash("You don't have permission to access Alert setup.", "danger")
        return redirect(url_for("main.index"))

    settings = AlertSettings.query.get(1)
    if not settings:
        settings = AlertSettings(id=1, support_emails="")
        db.session.add(settings)
        db.session.commit()

    form = AlertSettingsForm(obj=settings)

    if form.validate_on_submit():
        settings.support_emails = form.support_emails.data or ""
        db.session.commit()
        flash("Alert settings saved successfully.", "success")
        return redirect(url_for("alert_setup.index"))

    return render_template(
        "alert_setup/index.html",
        form=form,
        settings=settings,
    )
