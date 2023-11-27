import os
import re
from subprocess import Popen, PIPE
from stat import S_ISDIR, S_ISREG
import time
import datetime
import json
import random
import shutil
from urllib.parse import urljoin

# import getpass
from pathlib import Path
import tempfile

import requests
from paramiko import SSHClient, AutoAddPolicy
from loguru import logger

import pprint


def offset_to_est(dt_now: datetime.datetime):
    """Offset to EST time

    Args:
        dt_now (datetime.datetime): datetime.datetime.utcnow()

    Returns:
        datetime.datetime: EST datetime
    """
    est_norm_datetime = dt_now - datetime.timedelta(hours=4)
    return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")


STORAGE_PATH = os.path.join(Path("C:\\"), Path("eMARVault"))
IP_BLACKLISTED = "red - ip blacklisted"

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(STORAGE_PATH, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True,
)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)
        return False
    return True


mknewdir(STORAGE_PATH)

if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception(
            "Can't find manager_host in config.json. \
                Check that field and file exist."
        )
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


creds_file = "creds.json"
local_creds_json = os.path.join(STORAGE_PATH, creds_file)
logger.info(f"local_creds_json var is {local_creds_json}")


# create .ssh folder if doesn't exist with known_hosts inside
ssh_exists = mknewdir(os.path.join(Path().home(), ".ssh"))
if not ssh_exists:
    open(os.path.join(Path().home(), Path(".ssh/known_hosts")), "a").close()


class AppError(Exception):
    pass


class SSHConnectionError(Exception):
    pass


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

        filepath = (
            Path(STORAGE_PATH) / response.headers["Content-disposition"].split("=")[1]
        )
        print(filepath)
        with open(
            filepath,
            "wb",
        ) as msi:
            msi.write(response.content)
        print(response.status_code)
        # run agent.msi through install.cmd
        install_path = Path(STORAGE_PATH) / "install.cmd"
        with open(install_path, "w") as f:
            f.write(f"msiexec  /l* install.log /i {filepath}")

        Popen([install_path])
        logger.debug(
            "New msi version installed. From {} to {}",
            old_credentials["msi_version"],
            credentials["msi_version"],
        )
        # NOTE rerun PostInstallActions.ps1 after installation as Admin
        posha_path = os.path.join(
            Path("C:\\") / "Program Files" / "eMARVault" / "PostInstallActions.ps1"
        )
        posha_path_86 = os.path.join(
            Path("C:\\")
            / "Program Files (x86)"
            / "eMARVault"
            / "PostInstallActions.ps1"
        )
        posha_path_to_use = (
            posha_path_86 if os.path.isfile(posha_path_86) else posha_path
        )
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


def register_computer():
    import socket
    import platform

    computer_name = socket.gethostname()
    logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        computer_name = platform.node()
        logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        raise (
            ValueError(
                "Can't get computer name. Name {}, type {}",
                computer_name,
                type(computer_name),
            )
        )
    identifier_key = "new_computer"

    response = requests.post(
        f"{g_manager_host}/register_computer",
        json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        },
    )

    logger.debug(
        "response.request.method on /register_computer {}", response.request.method
    )

    if response.request.method == "GET":
        logger.warning(
            "Instead of POST method we have GET on /register_computer. \
                Retry with allow_redirects=False"
        )
        response = requests.post(
            f"{g_manager_host}/register_computer",
            allow_redirects=False,
            json={
                "computer_name": computer_name,
                "identifier_key": identifier_key,
            },
        )
        print("response.history", response.history)
        logger.debug(
            "Retry response.request.method on /register_computer. Method = {}",
            response.request.method,
        )

    if response.status_code == 200:
        logger.info(
            "New computer registered. Download will start next time \
                if credentials inserted to DB."
        )
    else:
        logger.warning(
            "Something went wrong. Response status code = {}", response.status_code
        )

    return response


def get_credentials():
    logger.info("Recieving credentials.")
    creds_json = None

    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")

        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
        )

        response = requests.post(
            f"{manager_host}/get_credentials",
            json={
                "computer_name": computer_name,
                "identifier_key": str(identifier_key),
            },
        )

        if response.status_code == 500 or response.status_code == 400:
            raise ConnectionAbortedError(response.text)

        if "rmcreds" in response.json():
            if os.path.isfile(local_creds_json):
                os.remove(local_creds_json)
                logger.warning(
                    "Remote server can't find computer {}. \
                        Deleting creds.json and registering current computer.",
                    computer_name,
                )
                register_computer()

    else:
        response = register_computer()

    if (
        response.json()["message"] == "Supplying credentials"
        or response.json()["message"] == "Computer registered"
    ):
        msi_version = (
            response.json()["msi_version"]
            if "msi_version" in response.json()
            else "stable"
        )
        with open(local_creds_json, "w") as f:
            json.dump(
                {
                    "computer_name": response.json()["computer_name"],
                    "identifier_key": response.json()["identifier_key"],
                    "manager_host": response.json()["manager_host"],
                    "msi_version": msi_version,
                },
                f,
            )
            logger.info(
                f"Full credentials recieved from server and {local_creds_json} updated."
            )

        creds_json = creds_json if creds_json else dict()

        return response.json(), creds_json

    else:
        raise ValueError(
            "Wrong response data. Can't proceed without correct credentials."
        )


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
    new_backup_name = searching_result.group(0) if searching_result else ''

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
                logger.error("Computer cannot connect to sftp: {}, computer:{}", e, credentials["computer_name"])
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


def download_file_from_pcc(credentials):
    """
    Download backup file from PCC API
    """

    # Set status as downloading
    logger.info("<-------Start downloading backup file from PCC API------->")
    update_download_status("downloading", credentials)
    est_datetime = datetime.datetime.fromisoformat(
        offset_to_est(datetime.datetime.utcnow())
    )
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

                filename = re.findall(
                    "filename=(.+)", res.headers["Content-Disposition"]
                )[0]
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


def send_activity(last_download_time, creds):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
        )
    else:
        manager_host = g_manager_host

    m_host = manager_host if "manager_host" not in creds else creds["manager_host"]

    url = f"{m_host}/last_time"
    requests.post(
        url,
        json={
            "computer_name": creds["computer_name"],
            "company_name": creds["company_name"],
            "identifier_key": creds["identifier_key"],
            "location_name": creds["location_name"],
            "last_download_time": last_download_time,
            "last_time_online": offset_to_est(datetime.datetime.utcnow()),
        },
    )
    logger.info("User last time download sent.")


def update_download_status(status, creds, last_downloaded="", last_saved_path=""):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
        )
    else:
        manager_host = g_manager_host

    m_host = manager_host if "manager_host" not in creds else creds["manager_host"]

    url = f"{m_host}/download_status"
    requests.post(
        url,
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


def create_desktop_icon():
    # This is path where the shortcut will be created
    path = r"C:\\Users\\Public\\Desktop\\eMARVault.lnk"
    icon_path = os.path.join(
        Path("C:\\") / "Program Files" / "eMARVault" / "eMARVault_256x256.ico"
    )
    icon_path_86 = os.path.join(
        Path("C:\\") / "Program Files (x86)" / "eMARVault" / "eMARVault_256x256.ico"
    )
    icon_path_to_use = icon_path_86 if os.path.isfile(icon_path_86) else icon_path

    if not os.path.exists(path):
        from win32com.client import Dispatch

        # directory to which the shortcut leads
        target = rf"{os.path.join(STORAGE_PATH, 'emar_backups.zip')}"
        wDir = rf"{STORAGE_PATH}"

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.IconLocation = str(icon_path_to_use)
        shortcut.WorkingDirectory = wDir
        shortcut.Targetpath = target
        shortcut.save()



@logger.catch
def main_func():
    logger.info("Downloading proccess started.")
    credentials, old_credentials = get_credentials()
    if not credentials:
        raise ValueError("Credentials not supplayed. Can't continue.")

    if credentials["status"] == "success":
        # Handle errors in files downloading and zip
        try:
            if not credentials.get("use_pcc_backup"):
                last_download_time = sftp_check_files_for_update_and_load(credentials)
            else:
                download_file_from_pcc(credentials)
                last_download_time = offset_to_est(datetime.datetime.utcnow())
            send_activity(last_download_time, credentials)
            logger.info("Downloading proccess finished.")
        except (AppError, FileNotFoundError):
            update_download_status("error", credentials)
            logger.info("Downloading process interrupted")

        # user = getpass.getuser()

        create_desktop_icon()

        self_update(STORAGE_PATH, credentials, old_credentials)

    elif credentials["status"] == "registered":
        logger.info(
            "New computer registered. Download will start next time if credentials available in DB."
        )

        create_desktop_icon()

    else:
        logger.info(
            f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}"
        )
        time.sleep(60)


try:
    # NOTE wait randomly from 0 to 1800 sec
    # to spread load on the server
    # NOTE: Check if this is the first script run
    is_first_run = not os.path.exists(STORAGE_PATH) or (
        len(os.listdir(STORAGE_PATH)) == 1
        and os.listdir(STORAGE_PATH)[0] == "emar_log.txt"
    )

    if not is_first_run:
        time.sleep(random.uniform(0, 1800))

    main_func()
    logger.info("Task finished")
    time.sleep(20)
except Exception as e:
    logger.error("Exception occurred: {}", e)
    time.sleep(120)
