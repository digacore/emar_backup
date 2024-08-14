import datetime
import os
import re
import shutil
import tempfile
from collections import namedtuple
from urllib.parse import urljoin

import requests

from app import schemas as s
from app.consts import COMPUTER_NAME, IDENTIFIER_KEY, MANAGER_HOST
from app.logger import logger
from app.utils.send_activity import offset_to_est
from app.utils.sftp_check_files_for_update_and_load import (
    AppError,
    add_file_to_zip,
    update_download_status,
)

Location = namedtuple("Location", ["location_name", "pcc_fac_id"])


def create_location_list_for_pcc(credentials: s.ConfigFile):
    loc = Location(credentials.location_name, credentials.pcc_fac_id)
    if loc.location_name.strip() == "":
        raise ValueError("Location name is empty.")
    locations_list = [loc]
    for location in credentials.additional_locations:
        if location.name == "":
            continue
        loc = Location(location.name, location.pcc_fac_id)
        locations_list.append(loc)
    return locations_list


def download_file_from_pcc(credentials: s.ConfigFile):
    """
    Download backup file from PCC API
    """

    # Set status as downloading
    logger.info("<-------Start downloading backup file from PCC API------->")
    update_download_status("downloading", credentials)
    est_datetime = datetime.datetime.fromisoformat(offset_to_est(datetime.datetime.utcnow()))
    download_dir = f"emarbackup_{est_datetime.strftime('%Y-%m-%d-%H-%M')}"
    locations = create_location_list_for_pcc(credentials)
    # Create temp directory to save downloaded backup and zip it
    with tempfile.TemporaryDirectory() as raw_tempdir:
        for loc in locations:
            # this split is required to remove temp string from dir name
            download_dir_path = os.path.join(raw_tempdir, loc.location_name.strip(), download_dir)
            if not os.path.exists(download_dir_path):
                os.makedirs(download_dir_path, exist_ok=True)
            last_saved_path = ""

            # Download backup file
            server_route = "pcc_api/download_backup"
            url = urljoin(MANAGER_HOST, server_route)
            data = s.GetPccDownloadData(
                computer_name=COMPUTER_NAME,
                identifier_key=IDENTIFIER_KEY,
                pcc_fac_id=loc.pcc_fac_id,
            )
            try:
                with requests.post(
                    url,
                    json=data.model_dump(),
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
        last_saved_path = add_file_to_zip(credentials, raw_tempdir)

    update_download_status(
        "downloaded",
        credentials,
        last_downloaded=str(download_dir_path),
        last_saved_path=last_saved_path,
    )

    logger.info("<-------Finish downloading backup file from PCC API------->")
