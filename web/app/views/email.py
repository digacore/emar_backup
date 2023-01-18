from flask import flash, redirect, url_for, render_template, request, Blueprint
from flask_login import login_required

from app import sendgrid_client
from app.forms import EmailForm
from app.logger import logger


email_blueprint = Blueprint("email", __name__)


@email_blueprint.route("/email_alert", methods=["GET", "POST"])
@logger.catch
@login_required
def email_alert():

    form = EmailForm(request.form)
    print("form.validate_on_submit()", form.validate_on_submit())
    print("form.is_submitted()", form.is_submitted())
    if form.validate_on_submit():
        html_body = form.html_body.data if form.html_body.data else None
        reply_to_address = form.reply_to_address.data if form.reply_to_address.data else None

        sendgrid_client.send_email(
            form.from_email.data,
            form.to_addresses.data,
            form.subject.data,
            form.body.data,
            html_body=html_body,
            reply_to_address=reply_to_address
        )
        logger.info(f"Email sent from {form.from_email.data} to {form.to_addresses.data}. Subject: {form.subject.data}")
        flash("Email sent.", "success")
        return redirect(url_for("main.index"))
    elif form.is_submitted():
        flash("The given data was invalid.", "danger")
    return render_template("email/email_alert.html", form=form)
