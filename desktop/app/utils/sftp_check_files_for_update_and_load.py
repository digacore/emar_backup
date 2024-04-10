import datetime
import os
import pprint
import re
import tempfile
from collections import namedtuple
from pathlib import Path
from stat import S_ISDIR, S_ISREG
from subprocess import PIPE, Popen
from urllib.parse import urljoin

import requests
from paramiko import AutoAddPolicy, SSHClient, SSHException, SFTPAttributes, SFTPClient

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
    ZIP_PATH = os.path.join(STORAGE_PATH, "emar_backups.zip")

    sub_paths = []
    for file in os.listdir(tempdir):
        sub_paths.append(os.path.join(tempdir, file))
    # TODO: check if zip_name exists and 7z.exe exists
    process = Popen(
        [
            Path(".") / "7z.exe",
            "a",
            f"-p{credentials.folder_password}",
            ZIP_PATH,
        ]
        + sub_paths,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout_res, stderr_res = process.communicate()

    # Check if archive can be changed by 7z and it is not corrupted
    stdout_str = stdout_res.decode()
    if "is not supported archive" in stdout_str:
        logger.info(
            "{} is not supported archive. Create new zip and delete the old one.",
            ZIP_PATH,
        )

        # Create new zip archive and save pulled backup to it
        new_zip = os.path.join(STORAGE_PATH, "emar_backups_new.zip")
        new_subprs = Popen(
            [
                Path(".") / "7z.exe",
                "a",
                new_zip,
                tempdir,
                f"-p{credentials.folder_password}",
            ],
            stdout=PIPE,
            stderr=PIPE,
        )

        new_subprs.communicate()

        # Remove the original zip archive with backups and rename the new one
        os.remove(ZIP_PATH)
        os.rename(new_zip, ZIP_PATH)

    # Log the situation something happened with 7z operation and throw error
    elif not re.search("Everything is Ok", stdout_str):
        logger.error(
            "7z can't add archive to emar_backups and delete tmp. Stdout: {}. Stderr: {}.",
            stdout_res,
            stderr_res,
        )
        raise AppError("7z can't add archive to emar_backups")

    logger.info("Files zipped.")

    # proc = Popen(
    #     [Path(".") / "7z.exe", "l", "-bd", "-slt", ZIP_PATH],
    #     stdout=PIPE,
    # )
    # if proc.stdout:
    #     raw_list_stdout = [f for f in proc.stdout.read().decode().splitlines()]
    # else:
    #     raw_list_stdout = []
    # # NOTE f.split("Path = ")[1] is folder name
    # # NOTE datetime.datetime.strptime(raw_list_stdout[raw_list_stdout.index(f)+4].lstrip("Modified = ") , '%Y-%m-%d %H:%M:%S') is folder Modified parameter converted to datetime
    # files = {
    #     f.split("Path = ")[1]: datetime.datetime.strptime(
    #         raw_list_stdout[raw_list_stdout.index(f) + 4].lstrip("Modified = "),
    #         "%Y-%m-%d %H:%M:%S",
    #     )
    #     for f in raw_list_stdout
    #     if f.startswith("Path = ")
    # }
    # dirs = [i for i in files if "\\" not in i]
    # dirs.sort(key=lambda x: files[x])
    # pprint.pprint(f"dirs:\n{dirs}")

    # # TODO should we make this configurable?
    # if len(dirs) > 12:
    #     diff = len(dirs) - 12
    #     for dir_index in range(diff):
    #         process = Popen(
    #             [
    #                 Path(".") / "7z.exe",
    #                 "d",
    #                 ZIP_PATH,
    #                 dirs[dir_index],
    #                 "-r",
    #                 f"-p{credentials.folder_password}",
    #             ]
    #         )
    #         process.communicate()

    # proc = Popen(
    #     [Path(".") / "7z.exe", "l", "-ba", "-slt", ZIP_PATH],
    #     stdout=PIPE,
    # )
    # if proc.stdout:
    #     raw_list_stdout = [f for f in proc.stdout.read().decode().splitlines()]
    # else:
    #     raw_list_stdout = []
    # # NOTE f.split("Path = ")[1] is folder name
    # # NOTE datetime.datetime.strptime(raw_list_stdout[raw_list_stdout.index(f)+4].lstrip("Modified = ") , '%Y-%m-%d %H:%M:%S') is folder Modified parameter converted to datetime
    # files = {
    #     f.split("Path = ")[1]: datetime.datetime.strptime(
    #         raw_list_stdout[raw_list_stdout.index(f) + 4].lstrip("Modified = "),
    #         "%Y-%m-%d %H:%M:%S",
    #     )
    #     for f in raw_list_stdout
    #     if f.startswith("Path = ")
    # }
    # ddirs = [i for i in files if "\\" not in i]
    # ddirs.sort(key=lambda x: files[x])
    # pprint.pprint(f"after delete dirs:\n{ddirs}")

    # # Check if new downloaded backup is present in the emar_backups.zip
    # searching_result = re.search(r"(emarbackup_.*)$", tempdir)
    # new_backup_name = searching_result.group(0) if searching_result else ""

    # if not new_backup_name in dirs:  # noqa: E713
    #     logger.error(
    #         "The new downloaded backup {} was not founded in the emar_backups.zip",
    #         new_backup_name,
    #     )
    #     raise FileNotFoundError("The new downloaded backup was not found in the emar_backups.zip")

    # return os.path.join(ZIP_PATH, new_backup_name)
    return ZIP_PATH


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
                # tempdir = raw_tempdir.split("$$")[0]
                tempdir = raw_tempdir
                last_saved_path = ""

                counter_downloaded_files = 0

                for loc in locations:
                    download_directory = loc.sftp_folder_path

                    files_checksum = get_files_checksum(sftp, download_directory)
                    all_files_checksum.update(files_checksum)

                    for filepath in files_checksum:
                        if not is_need_to_download(filepath, files_checksum[filepath], credentials):
                            continue

                        remote_dir = "/".join(filepath.split("/")[:-1])

                        # get and create local temp directory if not exists
                        local_temp_emar_dir = os.path.join(tempdir, loc.location_name, Path(remote_dir))
                        local_file_path = os.path.join(local_temp_emar_dir, Path(filepath).name)
                        # # NOTE avoid creating directories inside main directory
                        # local_temp_emar_dir = tempdir

                        if not os.path.exists(local_temp_emar_dir):
                            os.makedirs(local_temp_emar_dir, exist_ok=True)

                        # get file from sftp server if it was changed
                        # TODO what if file in the root
                        sftp.get(filepath, local_file_path)
                        counter_downloaded_files += 1

                if counter_downloaded_files:
                    last_saved_path = add_file_to_zip(credentials, tempdir)

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
