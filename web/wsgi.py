#!/user/bin/env python
from app import create_app, db, models, forms
from app.controllers import register_base_alert_controls, get_pcc_2_legged_token


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


@app.cli.command()
def update_cl_stat():
    from app.controllers import update_companies_locations_statistic

    update_companies_locations_statistic()


@app.cli.command()
def daily_summary():
    from app.controllers import daily_summary

    daily_summary()


@app.cli.command()
def reset_alerts():
    from app.controllers import reset_alert_statuses

    reset_alert_statuses()


@app.cli.command()
def get_pcc_access_key():
    access_key = get_pcc_2_legged_token()
    print(access_key)


if __name__ == "__main__":
    app.run()
    register_base_alert_controls()
