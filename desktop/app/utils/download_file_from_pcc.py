import datetime
import os
import re
import shutil
import tempfile
from urllib.parse import urljoin

import requests
from app.logger import logger
from app.utils.send_activity import offset_to_est
from app.utils.sftp_check_files_for_update_and_load import (
    AppError,
    add_file_to_zip,
    update_download_status,
)


def download_file_from_pcc(credentials):
    """
    Download backup file from PCC API
    """

    # Set status as downloading
    logger.info("<-------Start downloading backup file from PCC API------->")
    update_download_status("downloading", credentials)
    est_datetime = datetime.datetime.fromisoformat(offset_to_est(datetime.datetime.utcnow()))
    download_dir = f"emarbackup_{est_datetime.strftime('%H-%M_%b-%d-%Y')}"

    # Create temp directory to save downloaded backup and zip it
    with tempfile.TemporaryDirectory() as raw_tempdir:
        # this split is required to remove temp string from dir name
        download_dir_path = os.path.join(raw_tempdir, download_dir)
        os.mkdir(download_dir_path)
        last_saved_path = ""

        # Download backup file
        server_route = "pcc_api/download_backup"
        url = urljoin(credentials["manager_host"], server_route)
        try:
            with requests.post(
                url,
                json={
                    "computer_name": credentials["computer_name"],
                    "identifier_key": credentials["identifier_key"],
                },
                stream=True,
            ) as res:
                res.raise_for_status()

                filename = re.findall("filename=(.+)", res.headers["Content-Disposition"])[0]
                filepath = os.path.join(download_dir_path, filename)
                with open(filepath, "wb") as f:
                    shutil.copyfileobj(res.raw, f)

        except Exception as e:
            logger.error("Exception occurred while downloading: {}", e)
            raise AppError("Can't download backup file from PCC API")

        # Zip downloaded backup file
        last_saved_path = add_file_to_zip(credentials, download_dir_path)

    update_download_status(
        "downloaded",
        credentials,
        last_downloaded=str(download_dir_path),
        last_saved_path=last_saved_path,
    )

    logger.info("<-------Finish downloading backup file from PCC API------->")
