import os

from flask import render_template, url_for
from flask_openapi3 import OpenAPI
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_mail import Mail


class MainIndexLink(MenuLink):
    def get_url(self):
        return url_for("main.index")


# instantiate extensions
login_manager = LoginManager()
db = SQLAlchemy()
migration = Migrate()
mail = Mail()
admin = Admin(template_mode="bootstrap4")


def create_app(environment="development"):

    from config import config
    from app.views import (
        main_blueprint,
        auth_blueprint,
        email_blueprint,
    )
    from app.api import (
        downloads_info_blueprint,
        api_email_blueprint,
        computer_blueprint,
        download_msi_blueprint,
        download_msi_fblueprint,
        search_column_blueprint,
        locations_company_blueprint,
        sftp_data_blueprint,
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
        Alert,
        AlertView,
        DesktopClient,
        DesktopClientView,
        ClientVersion,
        ClientVersionView,
        AlertControls,
        AlertControlsView,
    )

    # Instantiate app.
    app = OpenAPI(__name__)

    # Set app config.
    env = os.environ.get("FLASK_ENV", environment)
    app.config.from_object(config[env])
    config[env].configure(app)

    # Set up extensions.
    db.init_app(app)
    migration.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints.
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(email_blueprint)
    app.register_blueprint(download_msi_fblueprint)

    # Register api.
    app.register_api(downloads_info_blueprint)
    app.register_api(api_email_blueprint)
    app.register_api(computer_blueprint)
    app.register_api(download_msi_blueprint)
    app.register_api(search_column_blueprint)
    app.register_api(locations_company_blueprint)
    app.register_api(sftp_data_blueprint)

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
    admin.add_view(AlertView(Alert, db.session))
    admin.add_view(DesktopClientView(DesktopClient, db.session))
    admin.add_view(ClientVersionView(ClientVersion, db.session))
    admin.add_view(AlertControlsView(AlertControls, db.session))

    # Error handlers.
    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return render_template("error.html", error=exc), exc.code

    return app
