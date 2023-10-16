#!/user/bin/env python
import click
from datetime import timedelta

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
def fill_user_permission_items():
    from app.logger import logger

    logger.info("Start fill_user_permission_items")
    users = models.User.query.all()
    for user in users:
        if not user.asociated_with:
            user.role = models.UserRole.USER
            user.company_id = (
                models.Company.query.filter(models.Company.is_global.is_(True))
                .first()
                .id
            )
        elif user.asociated_with.lower() == "global-full":
            user.role = models.UserRole.ADMIN
            user.company_id = (
                models.Company.query.filter(models.Company.is_global.is_(True))
                .first()
                .id
            )
        elif user.asociated_with.lower() == "global-view":
            user.role = models.UserRole.USER
            user.company_id = (
                models.Company.query.filter(models.Company.is_global.is_(True))
                .first()
                .id
            )
        elif user.asociated_with in [
            company.name for company in models.Company.query.all()
        ]:
            user.role = models.UserRole.ADMIN
            user.company_id = (
                models.Company.query.filter_by(name=user.asociated_with).first().id
            )
        elif user.asociated_with in [
            location.name for location in models.Location.query.all()
        ]:
            user.role = models.UserRole.ADMIN
            user.company_id = (
                models.Location.query.filter_by(name=user.asociated_with)
                .first()
                .company_id
            )
            user.location.append(
                models.Location.query.filter_by(name=user.asociated_with).first()
            )
    db.session.commit()
    logger.info("Finish fill_user_permission_items")


@app.cli.command()
def send_email():
    from app import mail
    from app.logger import logger
    from flask_mail import Message
    from flask import render_template

    msg = Message(
        subject="ALERT! eMAR Computer is Offline",
        sender="alerts@emarvault.com",
        recipients=["dvorchyk.d.dev@gmail.com"],
    )

    computer = models.Computer.query.get(507)

    msg.html = render_template(
        "email/single-computer-alert-email.html",
        computer=computer,
        location=computer.location,
        error="Computer is offline",
        last_download_time=computer.last_download_time,
    )

    mail.send(msg)
    logger.info("Email sent")


@app.cli.command()
def send_company_group_email():
    from app import mail
    from app.logger import logger
    from flask_mail import Message
    from flask import render_template

    msg = Message(
        subject="ALERT! Primary eMAR Computers are Offline",
        sender="alerts@emarvault.com",
        recipients=["dvorchyk.d.dev@gmail.com"],
    )

    company = models.Company.query.get(89)
    computers = models.Computer.query.filter_by(company_id=89).all()

    msg.html = render_template(
        "email/company-and-group-alert-email.html",
        computers=computers,
        company=company,
        error="Computer is offline",
    )

    mail.send(msg)
    logger.info("Email sent")


if __name__ == "__main__":
    app.run()
    register_base_alert_controls()
