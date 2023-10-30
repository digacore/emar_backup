#!/user/bin/env python
import click
from datetime import timedelta

from app import create_app, db, models, forms
from app.controllers import get_pcc_2_legged_token


app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, m=models, f=forms)


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
def get_pcc_access_key():
    access_key = get_pcc_2_legged_token()
    print(access_key)


@app.cli.command()
def clean_old_logs():
    from app.controllers import clean_old_logs

    clean_old_logs()


@app.cli.command()
@click.option("--computer-name", type=str)
@click.option("--days", type=int)
def gen_backup_download_logs(computer_name: str | None = None, days: int | None = None):
    from app.controllers import gen_fake_backup_download_logs

    time_period = timedelta(days=days) if days else timedelta(days=30)

    if computer_name:
        computer = models.Computer.query.filter_by(computer_name=computer_name).first()

        gen_fake_backup_download_logs(computer, time_period)
    else:
        computers = models.Computer.query.all()

        for computer in computers:
            gen_fake_backup_download_logs(computer, time_period)


@app.cli.command()
@click.option("--computer-name", type=str)
@click.option("--days", type=int)
def gen_backup_periods_logs(computer_name: str | None = None, days: int | None = None):
    from app.controllers import gen_fake_backup_periods_logs

    time_period = timedelta(days=days) if days else timedelta(days=30)

    if computer_name:
        computer = models.Computer.query.filter_by(computer_name=computer_name).first()

        gen_fake_backup_periods_logs(computer, time_period)
    else:
        computers = models.Computer.query.all()

        for computer in computers:
            gen_fake_backup_periods_logs(computer, time_period)


@app.cli.command()
@click.argument("scan_record_id", type=int)
def scan_pcc_activations(scan_record_id: int):
    from app.controllers import scan_pcc_activations

    scan_pcc_activations(scan_record_id)


@app.cli.command()
def critical_alert_email():
    from app.controllers import send_critical_alert

    send_critical_alert()


@app.cli.command()
def primary_computer_alert_email():
    from app.controllers import send_primary_computer_alert

    send_primary_computer_alert()


@app.cli.command()
def daily_summary_email():
    from app.controllers import send_daily_summary

    send_daily_summary()


@app.cli.command()
def weekly_summary_email():
    from app.controllers import send_weekly_summary

    send_weekly_summary()


if __name__ == "__main__":
    app.run()
