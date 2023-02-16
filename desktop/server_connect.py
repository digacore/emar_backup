import os
from subprocess import Popen, PIPE
from stat import S_ISDIR, S_ISREG
import time
import datetime
import json
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
        dt_now (datetime.datetime): datetime.datetime.now()

    Returns:
        datetime.datetime: EST datetime
    """
    est_norm_datetime = dt_now - datetime.timedelta(hours=5)
    return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")


storage_path = os.path.join(Path("C:\\"), Path("EmarDir"))

log_format = "{time} - {name} - {level} - {message}"
logger.add(
    sink=os.path.join(storage_path, "emar_log.txt"),
    format=log_format,
    serialize=True,
    level="DEBUG",
    colorize=True)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)
        return False
    return True


mknewdir(storage_path)

if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Error: {e}")
        raise Exception("Can't find manager_host in config.json. Check that field and file exist.")
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


creds_file = "creds.json"
local_creds_json = os.path.join(storage_path, creds_file)
logger.info(f"local_creds_json var is {local_creds_json}")


# create .ssh folder if doesn't exist with known_hosts inside
ssh_exists = mknewdir(os.path.join(Path().home(), ".ssh"))
if not ssh_exists:
    open(os.path.join(Path().home(), Path(".ssh/known_hosts")), 'a').close()


def register_computer():
    import socket
    import platform

    computer_name = socket.gethostname()
    logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        computer_name = platform.node()
        logger.debug("Computer Name {}, type {}", computer_name, type(computer_name))
    if not isinstance(computer_name, str):
        raise (ValueError("Can't get computer name. Name {}, type {}", computer_name, type(computer_name)))
    identifier_key = "new_computer"

    response = requests.post(f"{g_manager_host}/register_computer", json={
        "computer_name": computer_name,
        "identifier_key": identifier_key,
    })

    logger.debug("response.request.method on /register_computer {}", response.request.method)

    if response.request.method == "GET":
        logger.warning("Instead of POST method we have GET on /register_computer. Retry with allow_redirects=False")
        response = requests.post(f"{g_manager_host}/register_computer", allow_redirects=False,  json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        })
        print("response.history", response.history)
        logger.debug("Retry response.request.method on /register_computer. Method = {}", response.request.method)

    if response.status_code == 200:
        logger.info("New computer registered. Download will start next time if credentials inserted to DB.")
    else:
        logger.warning("Something went wrong. Response status code = {}", response.status_code)

    print("else response.json()", response.json())
    return response


@logger.catch
def get_credentials():
    logger.info("Recieving credentials.")
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")

        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host

        response = requests.post(f"{manager_host}/get_credentials", json={
            "computer_name": computer_name,
            "identifier_key": str(identifier_key),
        })
        # print("if response.json()", response.json())

        if "rmcreds" in response.json():
            if os.path.isfile(local_creds_json):
                os.remove(local_creds_json)
                logger.warning("Remote server can't find computer {}. Deleting creds.json and registering current computer.", computer_name)
                register_computer()

    else:
        response = register_computer()

    if response.json()["message"] == "Supplying credentials" or response.json()["message"] == "Computer registered":
        with open(local_creds_json, "w") as f:
            json.dump(
                {
                    "computer_name": response.json()["computer_name"],
                    "identifier_key": response.json()["identifier_key"],
                    "manager_host": response.json()["manager_host"]
                },
                f
            )
            logger.info(f"Full credentials recieved from server and {local_creds_json} updated.")

        return response.json()

    else:
        raise ValueError("Wrong response data. Can't proceed without correct credentials.")


@logger.catch
def sftp_check_files_for_update_and_load(credentials):

    # key = path, value = checksum
    files_cheksum = {}
    print('credentials["files_checksum"]', type(credentials["files_checksum"]))
    pprint.pprint(credentials["files_checksum"])
    download_directory = credentials["sftp_folder_path"] if credentials["sftp_folder_path"] else None

    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        try:
            ssh.connect(
                credentials["host"],
                username=credentials["sftp_username"],
                password=credentials["sftp_password"],
                timeout=10,
                auth_timeout=10
            )
        except Exception as e:
            raise Exception(e)

        with ssh.open_sftp() as sftp:
            # get list of all files and folders on sftp server
            if download_directory:
                list_dirs = sftp.listdir_attr(download_directory) if download_directory else sftp.listdir_attr()
                dir_names = [f"./{download_directory}/{i.filename}" for i in list_dirs if S_ISDIR(i.st_mode)]
                file_paths = {f"./{download_directory}/{i.filename}": "-".join(i.longname.split()[4:8]) for i in list_dirs if S_ISREG(i.st_mode)}

            else:
                list_dirs = sftp.listdir_attr()
                dir_names = [i.filename for i in list_dirs if S_ISDIR(i.st_mode)]
                file_paths = {f"./{i.filename}": "-".join(i.longname.split()[4:8]) for i in list_dirs if S_ISREG(i.st_mode)}

            while len(dir_names) > 0:
                lvl_ins_dir_names = []
                lvl_ins_file_paths = {}

                for objname in dir_names:
                    sanitized_objname = objname.lstrip("./")
                    inside_dirs = sftp.listdir_attr(sanitized_objname)
                    ins_dir_names = [f"./{sanitized_objname}/{i.filename}" for i in inside_dirs if S_ISDIR(i.st_mode)]
                    ins_file_paths = {f"./{sanitized_objname}/{i.filename}": "-".join(i.longname.split()[4:8]) for i in inside_dirs if S_ISREG(i.st_mode)}
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
            est_datetime = datetime.datetime.fromisoformat(offset_to_est(datetime.datetime.now()))
            prefix = f"backup_{est_datetime.strftime('%Y-%b-%d %H_%M')}_"
            suffix = f"_timestamp{est_datetime.timestamp()}"

            with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix) as tempdir:
                trigger_download = False
                for filepath in files_cheksum:
                    if filepath not in credentials["files_checksum"]:
                        trigger_download = True
                    elif files_cheksum[filepath] not in credentials["files_checksum"][filepath]:
                        trigger_download = True
                        print('credentials["files_checksum"][filepath]', credentials["files_checksum"][filepath])
                if not trigger_download:
                    print("Files were NOT downloaded. Reason: no changes noticed.\n")
                else:
                    for filepath in files_cheksum:
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
                        local_temp_emar_dir = os.path.join(tempdir, Path(dirname)) if dirname else tempdir
                        if not os.path.exists(local_temp_emar_dir):
                            os.mkdir(local_temp_emar_dir)
                        print("local_temp_emar_dir", local_temp_emar_dir)

                        # get file from sftp server if it was changed
                        # TODO what if file in the root
                        print("files_cheksum[filepath]", files_cheksum[filepath])
                        sftp.chdir(dirname)
                        sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                        print(f"downloaded: {dirname}/{filename}\n")

                sftp.close()

                if trigger_download:
                    zip_name = os.path.join(storage_path, "emar_backups.zip")
                    print("zip_name", zip_name)
                    subprs = Popen([
                            Path(".") / "7z.exe",
                            "a",
                            zip_name,
                            tempdir,
                            f'-p{credentials["folder_password"]}'
                        ])
                    subprs.communicate()

                    logger.info("Files zipped.")

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    dirs = [i for i in files if "\\" not in i]
                    dirs.sort(key=lambda x: x.split("timestamp")[1])
                    pprint.pprint(f"dirs:\n{dirs}")

                    # TODO should we make this configurable?
                    if len(dirs) > 12:
                        diff = len(dirs) - 12
                        for dir_index in range(diff):
                            subprs = Popen([
                                    Path(".") / "7z.exe",
                                    "d",
                                    zip_name,
                                    dirs[dir_index],
                                    "-r",
                                    f'-p{credentials["folder_password"]}'
                                ])
                            subprs.communicate()

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    ddirs = [i for i in files if "\\" not in i]
                    ddirs.sort(key=lambda x: x.split("timestamp")[1])
                    pprint.pprint(f"after delete dirs:\n{ddirs}")

                else:
                    logger.info("Nothing to zip.")

                update_download_status("downloaded", credentials, last_downloaded=str(tempdir))

        response = requests.post(f"{credentials['manager_host']}/files_checksum", json={
                    "files_checksum": files_cheksum,
                    "identifier_key": str(credentials['identifier_key']),
                    "last_time_online": str(offset_to_est(datetime.datetime.now()))
                })
        logger.debug("files_cheksum sent to server. Response status code = {}", response.status_code)

    return offset_to_est(datetime.datetime.now())


@logger.catch
def send_activity(last_download_time, creds):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    m_host = manager_host if "manager_host" not in creds else creds["manager_host"]

    url = f"{m_host}/last_time"
    requests.post(url, json={
        "computer_name": creds["computer_name"],
        "company_name": creds["company_name"],
        "identifier_key": creds["identifier_key"],
        "location_name": creds["location_name"],
        "last_download_time": str(last_download_time),
        "last_time_online": str(offset_to_est(datetime.datetime.now()))
    })
    logger.info("User last time download sent.")


@logger.catch
def update_download_status(status, creds, last_downloaded=""):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    m_host = manager_host if "manager_host" not in creds else creds["manager_host"]

    url = f"{m_host}/download_status"
    requests.post(url, json={
        "company_name": creds["company_name"],
        "location_name": creds["location_name"],
        "download_status": status,
        "last_time_online": str(offset_to_est(datetime.datetime.now())),
        "identifier_key": creds["identifier_key"],
        "last_downloaded": last_downloaded
    })
    logger.info(f"Download status: {status}.")


@logger.catch
def main_func():
    logger.info("Downloading proccess started.")
    credentials = get_credentials()
    print("\ncredentials", credentials, "\n")
    if not credentials:
        raise ValueError("Credentials not supplayed. Can't continue.")

    if credentials["status"] == "success":
        last_download_time = sftp_check_files_for_update_and_load(credentials)
        # last_download_time = offset_to_est(datetime.datetime.now())  # TODO for testing purpose, remove in prod
        send_activity(last_download_time, credentials)
        logger.info("Downloading proccess finished.")

        # user = getpass.getuser()

        path = r"C:\\Users\\Public\\Public Desktop\\EMAR.lnk"  # This is where the shortcut will be created

        if not os.path.exists(path):

            from win32com.client import Dispatch

            target = fr"{os.path.join(storage_path, 'emar_backups.zip')}"  # directory to which the shortcut is created
            wDir = fr"{storage_path}"

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.WorkingDirectory = wDir
            shortcut.Targetpath = target
            shortcut.save()

    elif credentials["status"] == "registered":
        logger.info("New computer registered. Download will start next time if credentials available in DB.")

    else:
        logger.info(f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}")
        time.sleep(60)


try:
    main_func()
    print("Task finished")
    time.sleep(20)
except Exception as e:
    print(f"Exception occured: {e}")
    time.sleep(120)
