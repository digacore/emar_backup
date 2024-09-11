import os
from urllib.parse import urljoin
import requests

from pathlib import Path
from subprocess import Popen

from app import schemas as s

from app.logger import logger
from app.consts import MANAGER_HOST, STORAGE_PATH


def self_update(credentials: s.ConfigFile, old_credentials: s.ConfigFile) -> None:
    logger.info(
        "Updating EmarVault client to new version. From {} to {}",
        old_credentials.version,
        credentials.msi_version,
    )
    URL = urljoin(MANAGER_HOST, "msi_download_to_local")
    data = s.MsiDownloadData(
        name="custompass",
        version=credentials.version,
        flag=credentials.version,
        identifier_key=credentials.identifier_key,
        current_msi_version=old_credentials.version,
    )
    response = requests.post(
        URL,
        json=data.model_dump(),
    )

    filepath = Path(STORAGE_PATH) / response.headers["Content-disposition"].split("=")[1]
    logger.debug(
        "New msi version downloaded. From {} to {}. Filepath: {}",
        old_credentials.version,
        credentials.msi_version,
        filepath,
    )
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
    Popen(["powershell.exe", "-File", posha_path, "-verb", "runas"])

    logger.debug("Scheduled task updated.")
    URL = urljoin(MANAGER_HOST, "update_current_msi_version")
    update_response = requests.post(
        URL,
        json={
            "identifier_key": credentials.identifier_key,
            "current_msi_version": credentials.version,
        },
    )

    logger.debug(
        "Request to update current msi version sent. Response: {}, text: {}",
        update_response.status_code,
        update_response.text,
    )
