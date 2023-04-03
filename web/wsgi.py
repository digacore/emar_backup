#!/user/bin/env python
from app import create_app, db, models, forms


app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, m=models, f=forms)


@app.cli.command()
def check_and_alert():
    """
    CLI command for celery worker.
    Checks computers activity.
    Send email and change status if something went wrong.
    """
    from app.controllers import check_and_alert

    check_and_alert()


@app.cli.command()
def create_superuser():
    from app.controllers import create_superuser

    create_superuser()


@app.cli.command()
def empty_to_stable():
    from app.controllers import empty_to_stable

    empty_to_stable()


if __name__ == "__main__":
    app.run()
