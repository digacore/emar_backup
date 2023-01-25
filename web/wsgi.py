#!/user/bin/env python
from datetime import datetime, timedelta
import requests
from app import create_app, db, models, forms
from app.logger import logger
from config import BaseConfig as CFG


app = create_app()


# flask cli context setup
@app.shell_context_processor
def get_context():
    """Objects exposed here will be automatically available from the shell."""
    return dict(app=app, db=db, m=models, f=forms)


@app.cli.command()
def check_and_alert():
    """Get all computers from DB."""
    computers: list[models.Computer] = models.Computer.query.all()
    alert_url = CFG.MAIL_ALERTS

    off_30_min_computers = 0
    no_update_files_2h = 0

    for computer in computers:
        if computer.last_download_time < datetime.now() - timedelta(seconds=43200):
            # TODO put support email here to send and receive emails
            requests.post(alert_url, json={
                "alerted_target": computer.computer_name,
                "alert_status": "red",
                "from_email": "sup_send@eamil.com",
                "to_addresses": "sup_receive@eamil.com",
                "subject": f"Computer {computer.computer_name} 12 hours alert!",
                "body": f"Computer {computer.computer_name} had not download files for more then 12 hours.",
                "html_body": "",
                "reply_to_address": ""
                })
            logger.info(f"Computer {computer.computer_name} 12 hours alert sent.")

        if computer.last_time_online < datetime.now() - timedelta(seconds=43200):
            # TODO put support email here to send and receive emails
            requests.post(alert_url, json={
                "alerted_target": computer.computer_name,
                "alert_status": "red",
                "from_email": "sup_send@eamil.com",
                "to_addresses": "sup_receive@eamil.com",
                "subject": f"Computer {computer.computer_name} 12 hours offline alert!",
                "body": f"Computer {computer.computer_name} had not been online for more then 12 hours.",
                "html_body": "",
                "reply_to_address": ""
                })
            logger.info(f"Computer {computer.computer_name} 12 hours offline alert sent.")

        if computer.last_time_online < datetime.now() - timedelta(seconds=1800):
            off_30_min_computers += 1

        if computer.last_download_time < datetime.now() - timedelta(seconds=7200):
            no_update_files_2h += 1

    if off_30_min_computers == len(computers):
        # TODO put support email here to send and receive emails
        requests.post(alert_url, json={
            "alerted_target": "all",
            "alert_status": "red",
            "from_email": "sup_send@eamil.com",
            "to_addresses": "sup_receive@eamil.com",
            "subject": "All computers offline 30 min alert!",
            "body": "All computers are offline more then 30 minutes.",
            "html_body": "",
            "reply_to_address": ""
            })
        logger.info("All computers offline 30 min alert sent.")

    if no_update_files_2h == len(computers):
        # TODO put support email here to send and receive emails
        requests.post(alert_url, json={
            "alerted_target": "all",
            "alert_status": "red",
            "from_email": "sup_send@eamil.com",
            "to_addresses": "sup_receive@eamil.com",
            "subject": "No new files over 2 h alert!",
            "body": "No new files were downloaded by all computers for over 2 hours.",
            "html_body": "",
            "reply_to_address": ""
            })
        logger.info("No new files over 2 h alert sent.")


if __name__ == "__main__":
    app.run()
