from flask import flash, redirect, url_for, render_template, request, Blueprint
from flask_login import login_required
from flask_mail import Message

from app import mail
from app.forms import EmailForm
from app.models import Alert

from app.logger import logger


email_blueprint = Blueprint("email", __name__)


@email_blueprint.route("/email_alert", methods=["GET", "POST"])
@logger.catch
@login_required
def email_alert():

    form = EmailForm(request.form)

    if form.validate_on_submit():

        if "template" in request.form:
            if len(request.form["template"]) > 0:

                alert = Alert.query.filter_by(name=request.form["template"]).first()

                form.html_body.data = alert.html_body
                form.subject.data = alert.subject
                form.body.data = alert.body
                form.to_addresses.data = alert.to_addresses
                form.from_email.data = alert.from_email
                form.template.data = ""

                flash("Email populated.", "success")
                return render_template("email/email_alert.html", form=form)

        html_body = form.html_body.data if form.html_body.data else ""

        msg = Message(
            subject=form.subject.data,
            body=form.body.data,
            recipients=[form.to_addresses.data],
            html=html_body,
        )

        if form.from_email.data:
            msg.sender = form.from_email.data

        mail.send(msg)

        logger.info(
            "Email sent to {}. Subject: {}", form.to_addresses.data, form.subject.data
        )
        flash("Email sent.", "success")
        return redirect(url_for("main.index"))
    elif form.is_submitted():
        flash("The given data was invalid.", "danger")
    return render_template("email/email_alert.html", form=form)
