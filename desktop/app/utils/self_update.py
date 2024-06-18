import os
from urllib.parse import urljoin
import requests

from pathlib import Path
from subprocess import Popen

from app import schemas as s

from app.logger import logger
from app.consts import MANAGER_HOST, STORAGE_PATH


def self_update(credentials: s.ConfigFile, old_credentials: s.ConfigFile) -> None:
    logger.debug(
        "Compare version in self_update. {} ?= {}",
        credentials.msi_version,
        old_credentials.version,
    )

    # check if new or old version is None. If yes - convert to stable
    if not credentials.msi_version:
        credentials.msi_version = "stable"
    if not old_credentials.version:
        old_credentials.version = "stable"

    if credentials.msi_version != old_credentials.version:
        logger.info(
            "Updating EmarVault client to new version. From {} to {}",
            old_credentials.version,
            credentials.msi_version,
        )
        URL = urljoin(MANAGER_HOST, "msi_download_to_local")
        data = s.MsiDownloadData(
            name="custompass",
            version=credentials.msi_version,
            flag=credentials.msi_version,
            identifier_key=credentials.identifier_key,
            current_msi_version=old_credentials.version,
        )
        response = requests.post(
            URL,
            json=data.model_dump(),
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
            old_credentials.version,
            credentials.msi_version,
        )
        # NOTE rerun PostInstallActions.ps1 after installation as Admin
        posha_path = os.path.join(Path("C:\\") / "Program Files" / "eMARVault" / "PostInstallActions.ps1")
        # NOTE this not needed cause we moved to 64bit
        # posha_path_86 = os.path.join(Path("C:\\") / "Program Files (x86)" / "eMARVault" / "PostInstallActions.ps1")
        # posha_path_to_use = posha_path_86 if os.path.isfile(posha_path_86) else posha_path
        Popen(["powershell.exe", "-File", posha_path, "-verb", "runas"])
        logger.debug("Scheduled task updated.")
        URL = urljoin(MANAGER_HOST, "update_current_msi_version")
        update_response = requests.post(
            URL,
            json={
                "identifier_key": credentials.identifier_key,
                "current_msi_version": credentials.msi_version,
            },
        )

        logger.debug(
            "Request to update current msi version sent. Response: {}, text: {}",
            update_response.status_code,
            update_response.text,
        )
