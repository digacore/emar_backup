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
        # TODO temporary setup. Change activated to False and asociated_with to empty
        user = User(
            username=f"{users_name}-{unique_id}",
            email=users_email,
            # password=CFG.SSO_DEF_PASSWORD,
            password=uuid4(),
            # activated=True,
            # asociated_with="Test-Company",
        )
        user.save()
    if not user.activated:
        flash("This user is deactivated", "danger")
        return redirect(url_for("auth.login"))

    # Begin user session by logging the user in
    login_user(user)

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
        # TODO temporary setup. Change activated to False and asociated_with to empty
        user = User(
            username=str(result["name"]).lower().replace(" ", "-"),
            email=result["preferred_username"],
            # password=CFG.SSO_DEF_PASSWORD,
            password=uuid4(),
            # activated=True,
            # asociated_with="Test-Company",
        )
        user.save()
    if not user.activated:
        flash("This user is deactivated", "danger")
        return redirect(url_for("auth.login"))

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    flash("SSO login successful.", "success")
    return redirect(url_for("main.index"))


# NOTE this could be useful for APIs

# @auth_blueprint.route("/call_downstream_api")
# def call_downstream_api():
#     token = auth.get_token_for_user(CFG.MICRO_SCOPE)
#     if "error" in token:
#         return redirect(url_for("auth.login"))
#     # Use access token to call downstream api
#     api_result = requests.get(
#         CFG.MICRO_ENDPOINT,
#         headers={"Authorization": "Bearer " + token["access_token"]},
#         timeout=30,
#     ).json()
#     return render_template("index.html", result=api_result)


# NOTE for API directly with token usage

# from flask import session
# import google.oauth2.credentials
# import google_auth_oauthlib.flow

# # This variable specifies the name of a file that contains the OAuth 2.0
# # information for this application, including its client_id and client_secret.
# CLIENT_SECRETS_FILE = "client_secret_556.json"

# # This OAuth 2.0 access scope allows for full read/write access to the
# # authenticated user's account and requires requests to use an SSL connection.
# SCOPES = [
#     "https://www.googleapis.com/auth/drive.metadata.readonly",
#     "openid",
#     "https://www.googleapis.com/auth/userinfo.email",
#     "https://www.googleapis.com/auth/userinfo.profile",
# ]
# API_SERVICE_NAME = "drive"
# API_VERSION = "v2"

# @auth_blueprint.route("/gauthorize")
# def gauthorize():
#     # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
#     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#         CLIENT_SECRETS_FILE, scopes=SCOPES
#     )

#     # The URI created here must exactly match one of the authorized redirect URIs
#     # for the OAuth 2.0 client, which you configured in the API Console. If this
#     # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
#     # error.
#     flow.redirect_uri = url_for("auth.oauth2callback", _external=True)
#     logger.debug("flow.redirect_uri {}", flow.redirect_uri)

#     authorization_url, state = flow.authorization_url(
#         # Enable offline access so that you can refresh an access token without
#         # re-prompting the user for permission. Recommended for web server apps.
#         access_type="offline",
#         # Enable incremental authorization. Recommended as a best practice.
#         include_granted_scopes="true",
#     )

#     # Store the state so the callback can verify the auth server response.
#     session["state"] = state
#     logger.debug("authorization_url {}", authorization_url)

#     return redirect(authorization_url)


# @auth_blueprint.route("/oauth2callback")
# def oauth2callback():
#     # Specify the state when creating the flow in the callback so that it can
#     # verified in the authorization server response.
#     state = session["state"]

#     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
#         CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
#     )
#     flow.redirect_uri = url_for("auth.oauth2callback", _external=True)

#     # Use the authorization server's response to fetch the OAuth 2.0 tokens.
#     authorization_response = request.url
#     flow.fetch_token(authorization_response=authorization_response)

#     # Store credentials in the session.
#     # ACTION ITEM: In a production app, you likely want to save these
#     #              credentials in a persistent database instead.
#     credentials = flow.credentials
#     session["credentials"] = credentials_to_dict(credentials)
#     flash("SSO login successful.", "success")
#     return redirect(url_for("main.index"))


# @auth_blueprint.route("/revoke")
# def revoke():
#     if "credentials" not in session:
#         return (
#             'You need to <a href="/gauthorize">authorize</a> before '
#             + "testing the code to revoke credentials."
#         )

#     credentials = google.oauth2.credentials.Credentials(**session["credentials"])

#     revoke = requests.post(
#         "https://oauth2.googleapis.com/revoke",
#         params={"token": credentials.token},
#         headers={"content-type": "application/x-www-form-urlencoded"},
#     )

#     status_code = getattr(revoke, "status_code")
#     if status_code == 200:
#         return "Credentials successfully revoked." + print_index_table()
#     else:
#         return "An error occurred." + print_index_table()


# @auth_blueprint.route("/clear")
# def clear_credentials():
#     if "credentials" in session:
#         del session["credentials"]
#     return "Credentials have been cleared.<br><br>" + print_index_table()


# def credentials_to_dict(credentials):
#     return {
#         "token": credentials.token,
#         "refresh_token": credentials.refresh_token,
#         "token_uri": credentials.token_uri,
#         "client_id": credentials.client_id,
#         "client_secret": credentials.client_secret,
#         "scopes": credentials.scopes,
#     }
