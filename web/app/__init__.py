import os
import json

# from datetime import datetime, timedelta

from flask import render_template, url_for
from flask_openapi3 import OpenAPI
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import generate_csrf
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from oauthlib.oauth2 import WebApplicationClient
from flask_session import Session

from app.utils import update_report_data

from config import BaseConfig as CFG


class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("main.index")


# instantiate extensions
login_manager = LoginManager()
db = SQLAlchemy()
migration = Migrate()
mail = Mail()
admin = Admin(template_mode="bootstrap4")
jwt = JWTManager()
google_client = WebApplicationClient(CFG.GOOGLE_CLIENT_ID)
flask_session = Session()


def create_app(environment="development"):

    from config import config
    from app.views import (
        main_blueprint,
        auth_blueprint,
        info_blueprint,
        company_blueprint,
        location_blueprint,
        pcc_blueprint,
        search_blueprint,
        merge_blueprint,
    )
    from app.api import (
        downloads_info_blueprint,
        computer_blueprint,
        download_msi_blueprint,
        download_msi_fblueprint,
        pcc_api_blueprint,
    )
    from app.models import (
        User,
        UserView,
        AnonymousUser,
        Company,
        CompanyView,
        Computer,
        ComputerView,
        Location,
        LocationView,
        LocationGroup,
        LocationGroupView,
        DesktopClient,
        DesktopClientView,
        ClientVersion,
        ClientVersionView,
    )

    # Instantiate app.
    app = OpenAPI(__name__)

    # to have access to real IPs from incoming requests
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Set app config.
    env = os.environ.get("FLASK_ENV", environment)
    app.config.from_object(config[env])
    config[env].configure(app)

    # basic config for flask-session
    app.secret_key = CFG.SECRET_KEY
    flask_session.init_app(app)

    # Set up extensions.
    db.init_app(app)
    migration.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)

    # Pass functions to jinja2 templates
    app.jinja_env.globals.update(offset_to_east=CFG.offset_to_est)
    app.jinja_env.globals.update(to_json=json.dumps)
    app.jinja_env.globals.update(update_report_data=update_report_data)
    app.jinja_env.globals.update(csrf_token=generate_csrf)
    # app.jinja_env.globals.update(datetime=datetime)
    # app.jinja_env.globals.update(timedelta=timedelta)

    # Register blueprints.
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(download_msi_fblueprint)
    app.register_blueprint(info_blueprint)
    app.register_blueprint(pcc_blueprint)
    app.register_blueprint(search_blueprint)
    app.register_blueprint(merge_blueprint)
    app.register_blueprint(company_blueprint)
    app.register_blueprint(location_blueprint)

    # Register api.
    app.register_api(downloads_info_blueprint)
    app.register_api(computer_blueprint)
    app.register_api(download_msi_blueprint)
    app.register_api(pcc_api_blueprint)

    # Set up flask login.
    @login_manager.user_loader
    def get_user(id):
        return User.query.filter_by(id=id).first()

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.anonymous_user = AnonymousUser

    # set optional bootswatch theme
    # NOTE flatly and litera - green one, good one
    # NOTE pulse and simplex,  yeti - white-black, distinct
    # NOTE sandstone - grey and green text, distinct
    # NOTE spacelab - grey and blue text, distinct
    # NOTE superhero - grey backround and white text, distinct
    # NOTE united - cherry navbar and red and black text, distinct
    # app.config["FLASK_ADMIN_SWATCH"] = "emar"
    app.config["FLASK_ADMIN_FLUID_LAYOUT"] = True

    # Flask-Mail
    mail.init_app(app)

    # Flask-Admin
    admin.init_app(
        app,
    )
    admin.name = app.config["APP_NAME"]
    # Add administrative views here
    admin.add_link(MainIndexLink(name="Main Page"))
    admin.add_view(UserView(User, db.session))
    admin.add_view(CompanyView(Company, db.session))
    admin.add_view(ComputerView(Computer, db.session))
    admin.add_view(LocationView(Location, db.session))
    admin.add_view(DesktopClientView(DesktopClient, db.session))
    admin.add_view(ClientVersionView(ClientVersion, db.session))
    admin.add_view(LocationGroupView(LocationGroup, db.session))

    # Error handlers.
    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return render_template("error.html", error=exc), exc.code

    return app
