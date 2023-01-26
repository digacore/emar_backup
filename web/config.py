import os
from dotenv import load_dotenv


load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))


class BaseConfig(object):
    """Base configuration."""

    APP_NAME = "Management Flask App"
    DEBUG_TB_ENABLED = False
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "Ensure you set a secret key, this is important!"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False

    ALERT_PERIOD = int(os.environ.get("ALERT_PERIOD", 300))

    MAIL_ALERTS = os.environ.get("MAIL_ALERTS")
    SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")
    TO_ADDRESSES = os.environ.get("TO_ADDRESSES")

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
    WTF_CSRF_ENABLED = False  # TODO validation fails when wtf csrf enabled


config = dict(
    development=DevelopmentConfig, testing=TestingConfig, production=ProductionConfig
)
