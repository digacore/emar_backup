import datetime
import os
import re
import pprint
import requests
import json
import tempfile

from urllib.parse import urljoin
from pathlib import Path
from subprocess import Popen, PIPE
from paramiko import SSHClient, AutoAddPolicy

from app import logger
from app.consts import IP_BLACKLISTED, LOCAL_CREDS_JSON, G_MANAGER_HOST, STORAGE_PATH
from stat import S_ISDIR, S_ISREG

from app.utils.send_activity import offset_to_est


class AppError(Exception):
    pass


class SSHConnectionError(Exception):
    pass


def update_download_status(status, creds, last_downloaded="", last_saved_path=""):
    if os.path.isfile(LOCAL_CREDS_JSON):
        with open(LOCAL_CREDS_JSON, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {LOCAL_CREDS_JSON}.")
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else G_MANAGER_HOST
        )
    else:
        manager_host = G_MANAGER_HOST

    m_host = manager_host if "manager_host" not in creds else creds["manager_host"]

    URL = urljoin(m_host, "download_status")
    requests.post(
        URL,
        json={
            "company_name": creds["company_name"],
            "location_name": creds["location_name"],
            "download_status": status,
            "last_time_online": offset_to_est(datetime.datetime.utcnow()),
            "identifier_key": creds["identifier_key"],
            "last_downloaded": last_downloaded,
            "last_saved_path": last_saved_path,
        },
    )
    logger.info(f"Download status: {status}.")


def add_file_to_zip(credentials: dict, tempdir: str) -> str:
    """
    Add new downloaded backup to the emar_backups.zip
    """
    zip_name = os.path.join(STORAGE_PATH, "emar_backups.zip")
    print("zip_name", zip_name)
    subprs = Popen(
        [
            Path(".") / "7z.exe",
            "a",
            zip_name,
            tempdir,
            f'-p{credentials["folder_password"]}',
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout_res, stderr_res = subprs.communicate()

    # Check if archive can be changed by 7z and it is not corrupted
    stdout_str = str(stdout_res)
    if re.search("is not supported archive", stdout_str):
        logger.info(
            "{} is not supported archive. Create new zip and delete the old one.",
            zip_name,
        )

        # Create new zip archive and save pulled backup to it
        new_zip = os.path.join(STORAGE_PATH, "emar_backups_new.zip")
        new_subprs = Popen(
            [
                Path(".") / "7z.exe",
                "a",
                new_zip,
                tempdir,
                f'-p{credentials["folder_password"]}',
            ],
            stdout=PIPE,
            stderr=PIPE,
        )

        new_subprs.communicate()

        # Remove the original zip archive with backups and rename the new one
        os.remove(zip_name)
        os.rename(new_zip, zip_name)

    # Log the situation something happened with 7z operation and throw error
    elif not re.search("Everything is Ok", stdout_str):
        logger.error(
            "7z can't add archive to emar_backups and delete tmp. Stdout: {}. Stderr: {}.",
            stdout_res,
            stderr_res,
        )
        raise AppError("7z can't add archive to emar_backups")

    logger.info("Files zipped.")

    proc = Popen(
        [Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name],
        stdout=PIPE,
    )
    if proc.stdout:
        raw_list_stdout = [f for f in proc.stdout.read().decode().splitlines()]
    else:
        raw_list_stdout = []
    # NOTE f.split("Path = ")[1] is folder name
    # NOTE datetime.datetime.strptime(raw_list_stdout[raw_list_stdout.index(f)+4].lstrip("Modified = ") , '%Y-%m-%d %H:%M:%S') is folder Modified parameter converted to datetime
    files = {
        f.split("Path = ")[1]: datetime.datetime.strptime(
            raw_list_stdout[raw_list_stdout.index(f) + 4].lstrip("Modified = "),
            "%Y-%m-%d %H:%M:%S",
        )
        for f in raw_list_stdout
        if f.startswith("Path = ")
    }
    dirs = [i for i in files if "\\" not in i]
    dirs.sort(key=lambda x: files[x])
    pprint.pprint(f"dirs:\n{dirs}")

    # TODO should we make this configurable?
    if len(dirs) > 12:
        diff = len(dirs) - 12
        for dir_index in range(diff):
            subprs = Popen(
                [
                    Path(".") / "7z.exe",
                    "d",
                    zip_name,
                    dirs[dir_index],
                    "-r",
                    f'-p{credentials["folder_password"]}',
                ]
            )
            subprs.communicate()

    proc = Popen(
        [Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name],
        stdout=PIPE,
    )
    if proc.stdout:
        raw_list_stdout = [f for f in proc.stdout.read().decode().splitlines()]
    else:
        raw_list_stdout = []
    # NOTE f.split("Path = ")[1] is folder name
    # NOTE datetime.datetime.strptime(raw_list_stdout[raw_list_stdout.index(f)+4].lstrip("Modified = ") , '%Y-%m-%d %H:%M:%S') is folder Modified parameter converted to datetime
    files = {
        f.split("Path = ")[1]: datetime.datetime.strptime(
            raw_list_stdout[raw_list_stdout.index(f) + 4].lstrip("Modified = "),
            "%Y-%m-%d %H:%M:%S",
        )
        for f in raw_list_stdout
        if f.startswith("Path = ")
    }
    ddirs = [i for i in files if "\\" not in i]
    ddirs.sort(key=lambda x: files[x])
    pprint.pprint(f"after delete dirs:\n{ddirs}")

    # Check if new downloaded backup is present in the emar_backups.zip
    searching_result = re.search(r"(emarbackup_.*)$", tempdir)
    new_backup_name = searching_result.group(0) if searching_result else ""

    if not new_backup_name in dirs:
        logger.error(
            "The new downloaded backup {} was not founded in the emar_backups.zip",
            new_backup_name,
        )
        raise FileNotFoundError(
            "The new downloaded backup was not found in the emar_backups.zip"
        )

    return os.path.join(zip_name, new_backup_name)


def sftp_check_files_for_update_and_load(credentials):
    # key = path, value = checksum
    files_cheksum = {}
    print('credentials["files_checksum"]', type(credentials["files_checksum"]))
    pprint.pprint(credentials["files_checksum"])
    download_directory = (
        credentials["sftp_folder_path"] if credentials["sftp_folder_path"] else None
    )

    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        try:
            ssh.connect(
                credentials["host"],
                username=credentials["sftp_username"],
                password=credentials["sftp_password"],
                timeout=10,
                auth_timeout=10,
            )
        except Exception as e:
            if isinstance(e, TimeoutError):
                response = requests.post(
                    f'{credentials["manager_host"]}/special_status',
                    json={
                        "computer_name": credentials["computer_name"],
                        "identifier_key": credentials["identifier_key"],
                        "special_status": IP_BLACKLISTED,
                    },
                )
                logger.error(
                    "Computer cannot connect to sftp: {}, computer:{}",
                    e,
                    credentials["computer_name"],
                )
                raise SSHConnectionError("Can't connect to sftp server")
            else:
                logger.error("Exception occurred while connecting to sftp: {}", e)
                raise AppError("Can't connect to sftp server")

        with ssh.open_sftp() as sftp:
            # get list of all files and folders on sftp server
            if download_directory:
                list_dirs = (
                    sftp.listdir_attr(download_directory)
                    if download_directory
                    else sftp.listdir_attr()
                )
                dir_names = [
                    f"./{download_directory}/{i.filename}"
                    for i in list_dirs
                    if S_ISDIR(i.st_mode)
                ]
                file_paths = {
                    f"./{download_directory}/{i.filename}": "-".join(
                        i.longname.split()[4:8]
                    )
                    for i in list_dirs
                    if S_ISREG(i.st_mode)
                }

            else:
                list_dirs = sftp.listdir_attr()
                dir_names = [i.filename for i in list_dirs if S_ISDIR(i.st_mode)]
                file_paths = {
                    f"./{i.filename}": "-".join(i.longname.split()[4:8])
                    for i in list_dirs
                    if S_ISREG(i.st_mode)
                }

            while len(dir_names) > 0:
                lvl_ins_dir_names = []
                lvl_ins_file_paths = {}

                for objname in dir_names:
                    sanitized_objname = objname.lstrip("./")
                    inside_dirs = sftp.listdir_attr(sanitized_objname)
                    ins_dir_names = [
                        f"./{sanitized_objname}/{i.filename}"
                        for i in inside_dirs
                        if S_ISDIR(i.st_mode)
                    ]
                    ins_file_paths = {
                        f"./{sanitized_objname}/{i.filename}": "-".join(
                            i.longname.split()[4:8]
                        )
                        for i in inside_dirs
                        if S_ISREG(i.st_mode)
                    }
                    lvl_ins_dir_names.extend(ins_dir_names)
                    lvl_ins_file_paths.update(ins_file_paths)

                print("\nlvl_ins_dir_names: ")
                pprint.pprint(lvl_ins_dir_names)
                print("\nlvl_ins_file_paths: ")
                pprint.pprint(lvl_ins_file_paths)
                dir_names.clear()
                dir_names.extend(lvl_ins_dir_names)
                file_paths.update(lvl_ins_file_paths)

            print("\nfile_paths: ")
            pprint.pprint(file_paths)
            files_cheksum.update(file_paths)
            print("\ndir_names: ")
            pprint.pprint(dir_names)

            update_download_status("downloading", credentials)
            est_datetime = datetime.datetime.fromisoformat(
                offset_to_est(datetime.datetime.utcnow())
            )
            prefix = f"emarbackup_{est_datetime.strftime('%H-%M_%b-%d-%Y')}_splitpoint"

            with tempfile.TemporaryDirectory(prefix=prefix) as raw_tempdir:
                # this split is required to remove temp string from dir name
                tempdir = raw_tempdir.split("_splitpoint")[0]
                trigger_download = False
                last_saved_path = ""

                for filepath in files_cheksum:
                    if filepath not in credentials["files_checksum"]:
                        trigger_download = True
                    elif (
                        files_cheksum[filepath]
                        not in credentials["files_checksum"][filepath]
                    ):
                        trigger_download = True
                        print(
                            'credentials["files_checksum"][filepath]',
                            credentials["files_checksum"][filepath],
                        )
                if not trigger_download:
                    logger.debug(
                        "Files were NOT downloaded. Reason: no changes noticed."
                    )
                else:
                    for filepath in files_cheksum:
                        # NOTE avoid download of "receipt.txt". The file is empty
                        if "receipt.txt" in filepath:
                            continue
                        # chdir to be on top dir level
                        sftp.chdir(None)
                        # if download_directory != ".":
                        #     sftp.chdir(download_directory)
                        print(f"filepath: {filepath}")
                        dirpath: list = filepath.split("/")[1:-1]
                        print(f"dirpath: {dirpath}")
                        filename: str = filepath.split("/")[-1]
                        print(f"filename: {filename}")
                        dirname = "/".join(dirpath)
                        print(f"checking: {dirname}/{filename}")

                        # get and create local temp directory if not exists
                        local_temp_emar_dir = (
                            os.path.join(tempdir, Path(dirname)) if dirname else tempdir
                        )
                        # NOTE avoid creating directories inside main directory
                        local_temp_emar_dir = tempdir

                        if not os.path.exists(local_temp_emar_dir):
                            os.mkdir(local_temp_emar_dir)
                        print("local_temp_emar_dir", local_temp_emar_dir)

                        # get file from sftp server if it was changed
                        # TODO what if file in the root
                        print("files_cheksum[filepath]", files_cheksum[filepath])
                        sftp.chdir(dirname)
                        local_filename = (
                            dirname.replace("/", "-") + ".zip"
                            if len(dirname) > 0
                            else filename
                        )
                        sftp.get(
                            filename,
                            os.path.join(local_temp_emar_dir, local_filename),
                        )
                        print(f"downloaded: {dirname}/{filename} -- {local_filename}\n")

                sftp.close()

                if trigger_download:
                    last_saved_path = add_file_to_zip(credentials, tempdir)
                else:
                    logger.info("Nothing to zip.")

                update_download_status(
                    "downloaded",
                    credentials,
                    last_downloaded=str(tempdir),
                    last_saved_path=last_saved_path,
                )

        response = requests.post(
            f"{credentials['manager_host']}/files_checksum",
            json={
                "files_checksum": files_cheksum,
                "identifier_key": str(credentials["identifier_key"]),
                "last_time_online": offset_to_est(datetime.datetime.utcnow()),
            },
        )
        logger.debug(
            "files_cheksum sent to server. Response status code = {}",
            response.status_code,
        )

    return offset_to_est(datetime.datetime.utcnow())
