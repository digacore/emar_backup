import datetime
import os
import tempfile
from collections import namedtuple
from pathlib import Path
from stat import S_ISDIR, S_ISREG
from urllib.parse import urljoin

import requests
from paramiko import AutoAddPolicy, SFTPAttributes, SFTPClient, SSHClient, SSHException

from app import controllers as c
from app import schemas as s
from app.consts import IP_BLACKLISTED, MANAGER_HOST, STORAGE_PATH
from app.logger import logger
from app.utils.send_activity import offset_to_est

EXCLUDE_DOWNLOAD_FILES = ("receipt.txt",)


class AppError(Exception):
    pass


class SSHConnectionError(Exception):
    pass


def update_download_status(status: str, creds: s.ConfigFile, last_downloaded="", last_saved_path="", error_message=""):
    # TODO: for error logging feature put message in request if there an error and in web put this message in error.log
    credentials = s.ConfigFile.model_validate(creds)
    now = offset_to_est(datetime.datetime.utcnow())
    URL = urljoin(MANAGER_HOST, "download_status")
    data = s.DownloadStatusData(
        company_name=credentials.company_name,
        location_name=credentials.location_name,
        download_status=status,
        last_time_online=now,
        identifier_key=credentials.identifier_key,
        last_downloaded=last_downloaded,
        last_saved_path=last_saved_path,
        error_message=error_message,
    )
    requests.post(
        URL,
        json=data.model_dump(),
    )
    logger.info(f"Download status: {status}.")


def add_file_to_zip(credentials: s.ConfigResponse, tempdir: str) -> str:
    """
    Add new downloaded backup to the emar_backups.zip
    """
    logger.info("Entering function add_file_to_zip.")
    ZIP_PATH = os.path.join(STORAGE_PATH, "emar_backups.zip")
    archive = c.Archive(path=ZIP_PATH, password=credentials.folder_password)
    logger.info("Archive created. {}", ZIP_PATH)
    # adding file for its folder by location

    for file in os.listdir(tempdir):
        try:
            logger.info("Adding file {} to zip. {}", file, tempdir)
            archive.add_item(local_path=os.path.join(tempdir, file))
            logger.info("File {} added to zip.", file)
        except c.ArchiveException as e:
            if "is not supported archive" in str(e):
                logger.error("Archive is not supported. Creating new one.")
                # rename old archive
                renamed_archive_name = ZIP_PATH + ".old"
                if os.path.exists(renamed_archive_name):
                    # delete old archive
                    os.remove(renamed_archive_name)
                os.rename(ZIP_PATH, renamed_archive_name)
                archive = c.Archive(path=ZIP_PATH, password=credentials.folder_password)
                archive.add_item(local_path=os.path.join(tempdir, file))
        except Exception as e:
            logger.error("Exception occurred while adding file to zip: {}", e)
            raise AppError("Can't add file to zip")

    logger.info("Files zipped.")
    # Check if there are more than 12 backups in the emar_backups.zip
    for dir in archive.dir():
        dir_count = len(archive.dir(dir.name))
        last_path = archive.dir(dir.name)[0].name if dir_count > 0 else ""
        if dir_count > 12:
            logger.info("More than 12 backups for location {}. Deleting the oldest ones.", dir.name)
            diff = dir_count - 12
            for _ in range(diff):
                archive.delete(dir.name + "/" + archive.dir(dir.name)[0].name)

    return last_path


Location = namedtuple("Location", ["location_name", "sftp_folder_path"])


def create_location_list(credentials: s.ConfigFile) -> list[Location]:
    loc = Location(credentials.location_name, credentials.sftp_folder_path)
    if loc.location_name == "":
        raise ValueError("Location name is empty.")
    locations_list = [loc]
    for location in credentials.additional_locations:
        if location.name == "":
            continue
        loc = Location(location.name, location.default_sftp_path)
        locations_list.append(loc)
    return locations_list


def ssh_connect(ssh: SSHClient, credentials: s.ConfigResponse, port: int = 22):
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh.connect(
            hostname=credentials.host,
            username=credentials.sftp_username,
            password=credentials.sftp_password,
            timeout=10,
            auth_timeout=10,
            look_for_keys=False,
            port=port,
        )
    except TimeoutError:
        SPECIAL_STATUS_URL = urljoin(MANAGER_HOST, "special_status")
        data = s.SetSpecialStatus(
            computer_name=credentials.computer_name,
            identifier_key=credentials.identifier_key,
            special_status=IP_BLACKLISTED,
        )
        res = requests.post(
            SPECIAL_STATUS_URL,
            json=data.model_dump(),
        )
        res.raise_for_status()
        raise SSHConnectionError("Can't connect to sftp server")


def create_checksum(item: SFTPAttributes) -> str:
    return str(item.st_mtime)


def is_dir(item: SFTPAttributes) -> bool:
    return S_ISDIR(item.st_mode)


def is_file(item: SFTPAttributes) -> bool:
    return S_ISREG(item.st_mode)


def get_files_checksum(sftp: SFTPClient, directory: str = "") -> dict[str, str]:
    files_checksum = {}
    if not directory:
        directory = "."
    items = sftp.listdir_attr(directory)
    for item in items:
        if is_file(item):
            if item.filename not in EXCLUDE_DOWNLOAD_FILES:
                files_checksum[f"{directory}/{item.filename}"] = create_checksum(item)
        elif is_dir(item):
            files_checksum.update(get_files_checksum(sftp, f"{directory}/{item.filename}"))
    return files_checksum


def is_need_to_download(file_path: str, check_sum: str, credentials: s.ConfigResponse) -> bool:
    for file_path in credentials.files_checksum:
        if check_sum == credentials.files_checksum[file_path]:
            return False
    return True


def sftp_check_files_for_update_and_load(credentials: s.ConfigResponse):
    locations = create_location_list(credentials)
    with SSHClient() as ssh:
        try:
            ssh_connect(
                ssh,
                credentials=credentials,
                port=52222,
            )
        except SSHException as e:
            logger.error("Exception occurred while connecting to sftp: {}", e)
            raise AppError("Can't connect to sftp server")

        with ssh.open_sftp() as sftp:
            # get list of all files and folders on sftp server

            update_download_status("downloading", credentials)
            est_datetime = datetime.datetime.fromisoformat(offset_to_est(datetime.datetime.utcnow()))
            prefix = f"emarbackup_{est_datetime.strftime('%Y-%m-%d-%H-%M')}$$"

            all_files_checksum = {}

            with tempfile.TemporaryDirectory(prefix=prefix) as raw_tempdir:
                # this split is required to remove temp string from dir name
                marked_dir = prefix.split("$$")[0]
                tempdir = raw_tempdir
                last_saved_path = ""

                counter_downloaded_files = 0
                logger.info("Start iterate by location.")
                for loc in locations:
                    download_directory = loc.sftp_folder_path

                    files_checksum = get_files_checksum(sftp, download_directory)
                    all_files_checksum.update(files_checksum)

                    for filepath in files_checksum:
                        # if not is_need_to_download(filepath, files_checksum[filepath], credentials):
                        #     continue

                        # get and create local temp directory if not exists
                        local_temp_emar_dir = os.path.join(tempdir, loc.location_name, Path(marked_dir))
                        local_file_path = os.path.join(local_temp_emar_dir, Path(filepath).name)

                        if not os.path.exists(local_temp_emar_dir):
                            os.makedirs(local_temp_emar_dir, exist_ok=True)

                        # get file from sftp server
                        sftp.get(filepath, local_file_path)
                        counter_downloaded_files += 1

                if counter_downloaded_files:
                    logger.info("Start adding tempdir to zip.")
                    last_saved_path = add_file_to_zip(credentials, tempdir)
                    logger.info("Tempdir added to zip.")
        # sftp.close()

        update_download_status(
            "downloaded",
            credentials,
            last_downloaded=str(tempdir),
            last_saved_path=last_saved_path,
        )
        URL = urljoin(MANAGER_HOST, "files_checksum")
        response = requests.post(
            URL,
            json={
                "files_checksum": all_files_checksum,
                "identifier_key": str(credentials.identifier_key),
                "last_time_online": offset_to_est(datetime.datetime.utcnow()),
            },
        )
        logger.debug(
            "files_checksum sent to server. Response status code = {}",
            response.status_code,
        )

    return offset_to_est(datetime.datetime.utcnow())
