import json

from app.logger import logger
from app.consts import COMPSTAT_FILE


@logger.catch
def changes_lookup(comp_remote_data):
    with open(COMPSTAT_FILE, "w") as f:
        json.dump(
            {
                "sftp_host": comp_remote_data["sftp_host"],
                "sftp_username": comp_remote_data["sftp_username"],
                "sftp_folder_path": comp_remote_data["sftp_folder_path"],
                "manager_host": comp_remote_data["manager_host"],
                "msi_version": comp_remote_data["msi_version"],
            },
            f,
        )
        logger.info("Updated computer data was written to compstat.json")
