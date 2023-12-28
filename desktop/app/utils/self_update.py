import os
import requests

from pathlib import Path
from subprocess import Popen

from app.logger import logger


def self_update(STORAGE_PATH, credentials, old_credentials):
    logger.debug(
        "Compare version in self_update. {} ?= {}",
        credentials["msi_version"],
        old_credentials["msi_version"],
    )

    # check if new or old version is None. If yes - convert to stable
    if not credentials["msi_version"]:
        credentials["msi_version"] = "stable"
    if not old_credentials["msi_version"]:
        old_credentials["msi_version"] = "stable"

    if credentials["msi_version"] != old_credentials["msi_version"]:
        logger.info(
            "Updating EmarVault client to new version. From {} to {}",
            old_credentials["msi_version"],
            credentials["msi_version"],
        )
        response = requests.post(
            f"{credentials['manager_host']}/msi_download_to_local",
            json={
                "name": "custompass",  # TODO is this required?
                "version": credentials["msi_version"],
                "flag": credentials["msi_version"],
                "identifier_key": credentials["identifier_key"],
                "current_msi_version": old_credentials["msi_version"],
            },
        )

        filepath = Path(STORAGE_PATH) / response.headers["Content-disposition"].split("=")[1]
        print(filepath)
        with open(
            filepath,
            "wb",
        ) as msi:
            msi.write(response.content)

        Popen(["msiexec", "/i", filepath])
        logger.debug(
            "New msi version installed. From {} to {}",
            old_credentials["msi_version"],
            credentials["msi_version"],
        )
        # NOTE rerun PostInstallActions.ps1 after installation as Admin
        posha_path = os.path.join(Path("C:\\") / "Program Files" / "eMARVault" / "PostInstallActions.ps1")
        posha_path_86 = os.path.join(Path("C:\\") / "Program Files (x86)" / "eMARVault" / "PostInstallActions.ps1")
        posha_path_to_use = posha_path_86 if os.path.isfile(posha_path_86) else posha_path
        Popen(["powershell.exe", "-File", posha_path_to_use, "-verb", "runas"])
        logger.debug("Scheduled task updated.")

        update_response = requests.post(
            f"{credentials['manager_host']}/update_current_msi_version",
            json={
                "identifier_key": credentials["identifier_key"],
                "current_msi_version": credentials["msi_version"],
            },
        )

        logger.debug(
            "Request to update current msi version sent. Response: {}, text: {}",
            update_response.status_code,
            update_response.text,
        )
