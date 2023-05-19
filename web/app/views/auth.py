from datetime import datetime
import requests
import json
from uuid import uuid4

import identity
import identity.web

from flask import Blueprint, render_template, url_for, redirect, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.forms import LoginForm
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
                flash("Login successful.", "success")
                return redirect(url_for("main.index"))

            flash("This user is deactivated", "danger")
            return render_template("auth/login.html", form=form)

        flash("Wrong user ID or password.", "danger")
    return render_template("auth/login.html", form=form)


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
        )
        user.save()
    if not user.activated:
        flash("This user is deactivated", "danger")
        return redirect(url_for("auth.login"))

    # Begin user session by logging the user in
    login_user(user)
    user.last_time_online = CFG.offset_to_est(
        datetime.now().replace(microsecond=0), True
    )

    # Send user back to homepage
    flash("SSO login successful.", "success")
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

    # NOTE this one is for correct logout from microsoft sso
    auth.log_out(url_for("main.index", _external=True))
    return redirect(url_for("main.index"))


def get_google_provider_cfg():
    return requests.get(CFG.GOOGLE_DISCOVERY_URL).json()


@auth_blueprint.route("/mlogin")
def mlogin():
    auth_uri = auth.log_in(
        scopes=CFG.MICRO_SCOPE,  # Have user consent to scopes during log-in
        redirect_uri=url_for(
            "auth.auth_response", _external=True
        ),  # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
    )
    return redirect(auth_uri["auth_uri"])


@auth_blueprint.route(CFG.MICRO_REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        flash("Can't complete_log_in for current request", "danger")
        return render_template("auth/login.html", result=result)

    # check if result["preferred_username"] has email inside
    if "@" not in result["preferred_username"]:
        flash(f"Can't verify user {result['name']} email", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=result["preferred_username"]).first()

    # Create a user in our db with the information provided by Microsoft
    if not user:
        user = User(
            username=str(result["name"]).lower().replace(" ", "-"),
            email=result["preferred_username"],
            password=str(uuid4()),
        )
        user.save()
    if not user.activated:
        flash("This user is deactivated", "danger")
        return redirect(url_for("auth.login"))

    # Begin user session by logging the user in
    login_user(user)
    user.last_time_online = CFG.offset_to_est(
        datetime.now().replace(microsecond=0), True
    )

    # Send user back to homepage
    flash("SSO login successful.", "success")
    return redirect(url_for("main.index"))
