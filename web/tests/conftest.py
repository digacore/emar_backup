import pytest

from app import db, create_app
from app.controllers import init_db

app = create_app(environment="testing")
app.config["TESTING"] = True


@pytest.fixture
def client():

    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()
        db.drop_all()
        db.create_all()
        init_db(True)
        yield client
        db.session.remove()
        db.drop_all()
        app_ctx.pop()


@pytest.fixture
def test_db():

    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()
        db.drop_all()
        db.create_all()
        init_db(True)
        yield db
        db.session.remove()
        db.drop_all()
        app_ctx.pop()
