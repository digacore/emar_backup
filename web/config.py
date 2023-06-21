import os
import datetime
from dotenv import load_dotenv


load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))


class BaseConfig(object):
    """Base configuration."""

    APP_NAME = "eMAR Vault"
    DEBUG_TB_ENABLED = False
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "Ensure you set a secret key, this is important!"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    APP_HOST_URL = os.environ.get("APP_HOST_URL")

    SUPER_USER_PASS = os.environ.get("SUPERPASS")
    SUPER_USER_NAME = os.environ.get("SUPER_USER_NAME", "emarsuperuser")
    SUPER_USER_MAIL = os.environ.get("SUPERPASS", "emarsup@email.com")

    ALERT_PERIOD = int(os.environ.get("ALERT_PERIOD", 300))
    UPDATE_CL_PERIOD = int(os.environ.get("UPDATE_CL_PERIOD", 120))
    DAILY_SUMMARY_PERIOD = int(os.environ.get("DAILY_SUMMARY_PERIOD", 86400))

    MAIL_ALERTS = os.environ.get("MAIL_ALERTS", "/api_email_alert")
    SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")
    TO_ADDRESSES = os.environ.get("TO_ADDRESSES")

    # set optional bootswatch theme
    FLASK_ADMIN_SWATCH = "cerulean"

    # flask-mail config
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEFAULT_SENDER = os.environ.get("SUPPORT_EMAIL")

    USER_PERMISSIONS = [
        ("Global-full", "Global-full"),
        ("Global-view", "Global-view"),
    ]

    CLIENT_VERSIONS = [("stable", "stable"), ("latest", "latest")]

    DEFAULT_SFTP_HOST = os.environ.get("DEFAULT_SFTP_HOST", "ftpus.pointclickcare.com")
    DEFAULT_SFTP_USERNAME = os.environ.get("DEFAULT_SFTP_USERNAME", "Username")
    DEFAULT_SFTP_PASSWORD = os.environ.get("DEFAULT_SFTP_PASSWORD", "password")
    DEFAULT_FOLDER_PASSWORD = os.environ.get("DEFAULT_FOLDER_PASSWORD", "password")
    DEFAULT_MANAGER_HOST = os.environ.get(
        "DEFAULT_MANAGER_HOST", "https://emarvault.com/"
    )

    # developer and client emails to use in production testing
    DEV_EMAIL = os.environ.get("DEV_EMAIL", "dummy@dddevemail.com")
    CLIENT_EMAIL = os.environ.get("CLIENT_EMAIL", "dummy@cccevemail.com")

    # google sso config
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_DISCOVERY_URL = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

    # microsoft sso config
    MICRO_AUTHORITY = os.environ.get(
        "MICRO_AUTHORITY", "https://login.microsoftonline.com/common"
    )
    MICRO_CLIENT_ID = os.environ.get("MICRO_CLIENT_ID", None)
    MICRO_CLIENT_SECRET = os.environ.get("MICRO_CLIENT_SECRET", None)

    # You can find the proper permission names from this document
    # https://docs.microsoft.com/en-us/graph/permissions-reference
    MICRO_SCOPE = ["User.ReadBasic.All"]

    # Used for forming an absolute URL to your redirect URI.
    # The absolute URL must match the redirect URI you set
    # in the app's registration in the Azure portal.
    MICRO_REDIRECT_PATH = "/getAToken"

    # You can find more Microsoft Graph API endpoints from Graph Explorer
    # https://developer.microsoft.com/en-us/graph/graph-explorer
    # This resource requires no admin consent
    MICRO_ENDPOINT = "https://graph.microsoft.com/v1.0/users"

    # TODO default password when user is logged in through sso. Do we need it?
    SSO_DEF_PASSWORD = os.environ.get("SSO_DEF_PASSWORD", None)

    # NOTE special statuses. Transform to some object?
    SPECIAL_STATUSES = ["red - ip blacklisted"]

    def offset_to_est(dt_now: datetime.datetime, datetime_obj: bool = False):
        """Offset to EST time

        Args:
            dt_now (datetime.datetime): datetime.datetime.now()
            datetime_obj (bool): define what we need to return: str or datetime

        Returns:
            datetime.datetime: EST datetime
        """
        est_norm_datetime = dt_now - datetime.timedelta(hours=4)
        if datetime_obj:
            return est_norm_datetime.replace(microsecond=0)
        return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def configure(app):
        # Implement this method to do further configuration on your app.
        pass


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEVEL_DATABASE_URL",
        "sqlite:///" + os.path.join(base_dir, "database-devel.sqlite3"),
    )


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "sqlite:///" + os.path.join(base_dir, "database-test.sqlite3"),
    )


class ProductionConfig(BaseConfig):
    """Production configuration."""

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(base_dir, "database.sqlite3")
    )
    WTF_CSRF_ENABLED = True


config = dict(
    development=DevelopmentConfig, testing=TestingConfig, production=ProductionConfig
)
