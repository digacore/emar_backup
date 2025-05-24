from datetime import datetime
import requests
import json
from uuid import uuid4

from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    flash,
    request,
    make_response,
    session,
    abort,
)
import identity
import identity.web

from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from app.forms.auth import ChangeNotificationSettings
from app.models import User, UserPermissionLevel, UserRole
from app.forms import LoginForm, ChangePasswordForm
from app import google_client

from config import BaseConfig as CFG

from app.logger import logger


auth_blueprint = Blueprint("auth", __name__)

auth = identity.web.Auth(
    session=session,
    authority=CFG.MICRO_AUTHORITY,
    client_id=CFG.MICRO_CLIENT_ID,
    client_credential=CFG.MICRO_CLIENT_SECRET,
)


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
                session.permanent = True
                jwt_token = create_access_token(identity=form.user_id.data)
                refresh_jwt_token = create_refresh_token(identity=form.user_id.data)
                flash("Login successful.", "success")

                response = make_response(redirect(url_for("main.index")))
                response.set_cookie("jwt_token", jwt_token)
                response.set_cookie("refresh_jwt_token", refresh_jwt_token)
                return response

            flash(
                "This user is deactivated. Contact sales@emarvault.com to activate the account!",
                "danger",
            )
            return render_template("auth/login.html", form=form)
        else:
            flash("Invalid user ID or password.", "danger")
            logger.warning("Invalid user ID or password. {}", form.errors)
            return render_template("auth/login.html", form=form)
    logger.warning("Login error: {}", form.errors)
    flash("Login error", "danger")
    return render_template("auth/login.html", form=form)


@auth_blueprint.route("/change-password", methods=["POST"])
@login_required
def change_password():
    if (
        current_user.permission
        not in [UserPermissionLevel.GLOBAL, UserPermissionLevel.COMPANY]
        or current_user.role != UserRole.ADMIN
    ):
        abort(403, "You don't have permission to access this route.")

    form = ChangePasswordForm(request.form)
    if form.validate_on_submit():
        user: User = User.query.filter_by(id=form.user_id.data).first()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("user.edit_view", id=form.user_id.data))

        user.password = form.new_password.data
        user.update()
        flash("Password changed successfully.", "success")
        return redirect(url_for("user.edit_view", id=form.user_id.data))

    flash(f"Password was not changed. Reason: <{form.errors}>", "danger")
    return redirect(url_for("user.edit_view", id=form.user_id.data))


@auth_blueprint.route("/glogin", methods=["GET", "POST"])
def glogin():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    logger.debug("request.base_url {}", request.base_url)
    request_uri = google_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    logger.debug("request_uri {}", request_uri)
    return redirect(request_uri)


@auth_blueprint.route("/glogin/callback", methods=["GET", "POST"])
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(CFG.GOOGLE_CLIENT_ID, CFG.GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    google_client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = s.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User.query.filter_by(email=users_email).first()

    # Create a user in our db with the information provided
    # by Google
    if not user:
        user = User(
            username=f"{users_name}-{unique_id}",
            email=users_email,
            password=str(uuid4()),
            activated=False,
        )
        user.save()
        flash(
            "This user is deactivated. Contact sales@emarvault.com to activate the account!",
            "danger",
        )
        return redirect(url_for("auth.login"))
    elif user and user.is_deleted:
        user.is_deleted = False
        user.update()
        flash(
            "This user is deactivated. Contact Contact sales@emarvault.com to activate the account!",
            "danger",
        )
        return redirect(url_for("auth.login"))
    elif user and user.activated:
        # Begin user session by logging the user in
        login_user(user)
        user.last_time_online = CFG.offset_to_est(
            datetime.now().replace(microsecond=0), True
        )
        user.update()
        flash("Login successful.", "success")
        return redirect(url_for("main.index"))


@auth_blueprint.route("/logout")
@login_required
def logout():
    current_user.last_time_online = CFG.offset_to_est(
        datetime.now().replace(microsecond=0), True
    )
    current_user.update()
    logout_user()
    flash("You were logged out.", "info")

    response = make_response(redirect(url_for("main.index")))
    response.set_cookie("jwt_token", "", expires=0)
    return response


# route to refresh jwt token
@auth_blueprint.route("/refresh")
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    jwt_token = create_access_token(identity=current_user)
    response = make_response()
    response.set_cookie("jwt_token", jwt_token)
    return response
    # NOTE this one is for correct logout from microsoft sso
    auth.log_out(url_for("main.index", _external=True))
    return redirect(url_for("main.index"))


def get_google_provider_cfg():
    return requests.get(CFG.GOOGLE_DISCOVERY_URL).json()


@auth_blueprint.route("/mlogin")
def mlogin():
    redirect_url = url_for("auth.auth_response", _external=True)
    logger.info("Redirect URL: {}", redirect_url)
    auth_uri = auth.log_in(
        scopes=CFG.MICRO_SCOPE,  # Have user consent to scopes during log-in
        redirect_uri=redirect_url,  # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
    )
    logger.info("Auth URI: {}", auth_uri)
    return redirect(auth_uri["auth_uri"])


@auth_blueprint.route(CFG.MICRO_REDIRECT_PATH)
def auth_response():
    logger.info("Auth response received")
    result = auth.complete_log_in(request.args)
    form = LoginForm()
    if "error" in result:
        flash("Can't complete_log_in for current request", "danger")
        return render_template("auth/login.html", result=result, form=form)

    # check if result["preferred_username"] has email inside
    if "@" not in result["preferred_username"]:
        flash(f"Can't verify user {result['name']} email", "danger")
        return redirect(url_for("auth.login"))

    user = (
        User.query.with_deleted().filter_by(email=result["preferred_username"]).first()
    )
    # if user is deleted
    if user and user.is_deleted:
        user.is_deleted = False
        user.update()
        flash(
            "This user is deactivated. Contact sales@emarvault.com to activate the account!",
            "danger",
        )
        return redirect(url_for("auth.login"))

    # Create a user in our db with the information provided by Microsoft
    if not user:
        user = User(
            username=str(result["name"]).lower().replace(" ", "-"),
            email=result["preferred_username"],
            password=str(uuid4()),
            activated=False,
        )
        user.save()
    if not user.activated:
        flash(
            "This user is deactivated. Contact sales@emarvault.com to activate the account!",
            "danger",
        )
        return redirect(url_for("auth.login"))

    # Begin user session by logging the user in
    login_user(user)
    user.last_time_online = CFG.offset_to_est(
        datetime.now().replace(microsecond=0), True
    )
    user.update()

    # Send user back to homepage
    flash("SSO login successful.", "success")
    return redirect(url_for("main.index"))


@auth_blueprint.route("/notification-settings", methods=["POST"])
@login_required
def notification_settings():
    if (
        current_user.permission
        not in [UserPermissionLevel.GLOBAL, UserPermissionLevel.COMPANY]
        or current_user.role != UserRole.ADMIN
    ):
        abort(403, "You don't have permission to access this route.")

    form = ChangeNotificationSettings(request.form)
    if form.validate_on_submit():
        user: User = User.query.filter_by(id=form.user_id.data).first()

        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("user.edit_view", id=form.user_id.data))

        user.receive_alert_emails = form.receive_alert_emails.data
        user.receive_summaries_emails = form.receive_summaries_emails.data
        user.receive_device_test_emails = form.receive_device_test_emails.data
        user.update()
        flash("Notification settings changed successfully.", "success")
        return redirect(url_for("user.edit_view", id=form.user_id.data))

    flash(f"Notification settings was not changed. Reason: <{form.errors}>", "danger")
    return redirect(url_for("user.edit_view", id=form.user_id.data))
