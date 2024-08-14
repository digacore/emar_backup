import os
import datetime
import zoneinfo
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

    # TODO: remove APP_HOST_URL and use SERVER_NAME
    SERVER_NAME = os.environ.get("SERVER_NAME")
    APP_HOST_URL = os.environ.get("APP_HOST_URL")

    # Pagination
    DEFAULT_PAGE_SIZE = os.environ.get("DEFAULT_PAGE_SIZE", 10)
    PAGE_LINKS_NUMBER = os.environ.get("DEFAULT_PAGE_SIZE", 5)

    SUPER_USER_PASS = os.environ.get("SUPERPASS")
    SUPER_USER_NAME = os.environ.get("SUPER_USER_NAME", "emarsuperuser")
    SUPER_USER_MAIL = os.environ.get("SUPERPASS", "emarsup@email.com")

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

    CLIENT_VERSIONS = [("stable", "stable"), ("latest", "latest")]

    DEFAULT_SFTP_HOST = os.environ.get("DEFAULT_SFTP_HOST", "ftpus.pointclickcare.com")
    DEFAULT_SFTP_PORT = os.environ.get("DEFAULT_SFTP_PORT", "22")
    DEFAULT_SFTP_USERNAME = os.environ.get("DEFAULT_SFTP_USERNAME", "Username")
    DEFAULT_SFTP_PASSWORD = os.environ.get("DEFAULT_SFTP_PASSWORD", "password")
    DEFAULT_FOLDER_PASSWORD = os.environ.get("DEFAULT_FOLDER_PASSWORD", "password")
    DEFAULT_MANAGER_HOST = os.environ.get(
        "DEFAULT_MANAGER_HOST", "https://app.emarvault.com/"
    )

    # developer and client emails to use in production testing
    DEV_EMAIL = os.environ.get("DEV_EMAIL", "dummy@dddevemail.com")
    CLIENT_EMAIL = os.environ.get("CLIENT_EMAIL", "dummy@cccevemail.com")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "1234")
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(
        minutes=int(os.environ.get("EXPIRATION_TIME_JWT_AND_SESSION", 0))
    )

    # Flask-Session parameters
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(
        minutes=int(os.environ.get("EXPIRATION_TIME_JWT_AND_SESSION", 0))
    )
    SESSION_FILE_THRESHOLD = int(os.environ.get("SESSION_FILE_THRESHOLD", 500))
    SESSION_TYPE = "filesystem"

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

    # PCC API
    PCC_BASE_URL = os.environ.get("PCC_BASE_URL", None)
    PCC_CLIENT_ID = os.environ.get("PCC_CLIENT_ID", None)
    PCC_CLIENT_SECRET = os.environ.get("PCC_CLIENT_SECRET", None)
    PCC_APP_NAME = os.environ.get("PCC_APP_NAME", None)
    PCC_DAILY_QUOTA_LIMIT = int(os.environ.get("PCC_DAILY_QUOTA_LIMIT", 10000))
    CERTIFICATE_PATH = os.environ.get("CERTIFICATE_PATH", None)
    PRIVATEKEY_PATH = os.environ.get("PRIVATEKEY_PATH", None)
    GLOBAL_COMPANY_ID = os.environ.get("GLOBAL_COMPANY_ID", 1)

    # Logs deletion periods in days
    SYSTEM_LOGS_DELETION_PERIOD = int(
        os.environ.get("SYSTEM_LOGS_DELETION_PERIOD", 365)
    )
    COMPUTER_LOGS_DELETION_PERIOD = int(
        os.environ.get("COMPUTER_LOGS_DELETION_PERIOD", 90)
    )
    LOG_EVENT_DELETION_PERIOD = int(os.environ.get("LOG_EVENT_DELETION_PERIOD", 10))

    MAX_LOCATION_ACTIVE_COMPUTERS_LITE = int(
        os.environ.get("MAX_LOCATION_ACTIVE_COMPUTERS_LITE", 1)
    )
    MAX_LOCATION_ACTIVE_COMPUTERS_PRO = int(
        os.environ.get("MAX_LOCATION_ACTIVE_COMPUTERS_PRO", 5)
    )

    def offset_to_est(dt_now: datetime.datetime, datetime_obj: bool = False):
        """Offset to EST time

        Args:
            dt_now (datetime.datetime): datetime.datetime.now(timezone.utc)
            datetime_obj (bool): define what we need to return: str or datetime

        Returns:
            datetime.datetime: EST datetime (without specified tzinfo)
        """
        east_timezone = zoneinfo.ZoneInfo("America/New_York")

        # Set UTC timezone to dt_now
        dt_now = dt_now.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        est_norm_datetime = dt_now.astimezone(east_timezone)
        if datetime_obj:
            return est_norm_datetime.replace(microsecond=0, tzinfo=None)
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
    PCC_DAILY_QUOTA_LIMIT = int(os.environ.get("PCC_DAILY_QUOTA_LIMIT", 50000))


config = dict(
    development=DevelopmentConfig, testing=TestingConfig, production=ProductionConfig
)
