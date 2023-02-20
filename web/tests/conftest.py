import pytest

from app import db, create_app

app = create_app(environment="testing")
app.config["TESTING"] = True


@pytest.fixture
def client():

    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()
        db.drop_all()
        db.create_all()
        yield client
        db.session.remove()
        db.drop_all()
        app_ctx.pop()
