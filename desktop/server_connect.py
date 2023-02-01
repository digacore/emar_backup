import os
from subprocess import Popen, PIPE
import stat
import time
import datetime
import json
import hashlib
import requests
from pathlib import Path
import tempfile

from paramiko import SSHClient, AutoAddPolicy, AutoAddPolicy
from loguru import logger

storage_path = os.path.join(os.environ.get("APPDATA"), Path("EmarDir"))

log_format = "{time} - {name} - {level} - {message}"
# logger.add(sys.stdout, format=log_format, serialize=True, level="DEBUG", colorize=True)
# TODO for prod write to desktop
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
# local_creds_json = f"{os.getcwd()}\{creds_file}"
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
        raise(ValueError("Can't get computer name. Name {}, type {}", computer_name, type(computer_name)))
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
        print("if response.json()", response.json())

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

    # key = directory, value = file
    download_paths = {}
    files_cheksum = {}
    print('credentials["files_checksum"]', credentials["files_checksum"], type(credentials["files_checksum"]))
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

        update_download_status("connected to remote", credentials)

        with ssh.open_sftp() as sftp:
            # TODO recursive loop, rewrite
            update_download_status("comparing files", credentials)
            list_dir_path = credentials["sftp_folder_path"] if credentials["sftp_folder_path"] else "."
            for file_lvl_1 in sftp.listdir_attr(list_dir_path):
                # chdir to be on top dir level
                # logger.debug(f"Changing remote directory to start directory.")
                print("Changing remote directory to start directory.")
                sftp.chdir(None)
                sftp.chdir(download_directory)
                print("file_lvl_1", file_lvl_1.filename, file_lvl_1.st_mode, stat.S_ISDIR(file_lvl_1.st_mode))

                if not stat.S_ISDIR(file_lvl_1.st_mode):
                    # TODO handle repeated code 
                    if download_directory in download_paths:
                        download_paths[download_directory].append(file_lvl_1.filename)
                        stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                        checksum = stdout.read().decode()
                        files_cheksum[download_directory][file_lvl_1.filename] = checksum
                    else:
                        download_paths[download_directory] = [file_lvl_1.filename]
                        stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                        checksum = stdout.read().decode()
                        files_cheksum[download_directory] = {file_lvl_1.filename: checksum}

                elif stat.S_ISDIR(file_lvl_1.st_mode):
                    # logger.info(f"Changing remote directory to {file_lvl_1.filename}")
                    print(f"Changing remote directory to {file_lvl_1.filename}")
                    sftp.chdir(file_lvl_1.filename)

                    for file_lvl_2 in sftp.listdir_attr():
                        if not stat.S_ISDIR(file_lvl_2.st_mode):
                            # TODO handle repeated code 
                            if file_lvl_1.filename in download_paths:
                                download_paths[file_lvl_1.filename].append(file_lvl_2.filename)
                                stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_2.filename}")
                                checksum = stdout.read().decode()
                                print(f"{file_lvl_2.filename} checksum", checksum)
                                files_cheksum[file_lvl_1.filename][file_lvl_2.filename] = checksum
                            else:
                                download_paths[file_lvl_1.filename] = [file_lvl_2.filename]
                                stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_2.filename}")
                                checksum = stdout.read().decode()
                                print(f"{file_lvl_2.filename} checksum", checksum)
                                files_cheksum[file_lvl_1.filename] = {file_lvl_2.filename: checksum}

                else:
                    logger.error(f"Something went wrong during check of {file_lvl_1.filename}")
                    continue
        update_download_status("files compared", credentials)
        response = requests.post(f"{credentials['manager_host']}/files_checksum", json={
            "files_checksum": files_cheksum,
            "identifier_key": str(credentials['identifier_key']),
            "last_time_online": str(datetime.datetime.now())
        })
        print("files_cheksum", files_cheksum, type(files_cheksum))
        logger.debug("files_cheksum sent to server. Response status code = {}", response.status_code)

        sftp_check_download(
            download_paths=download_paths,
            credentials=credentials
        )

    return datetime.datetime.now()


def sftp_check_download(download_paths: dict, credentials: dict):
    from pprint import pprint
    pprint(f"download_paths {download_paths}")
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
            update_download_status("downloading", credentials)
            prefix=f"backup_{time.ctime()}_".replace(":", "-").replace(" ", "_")
            suffix=f"_timestamp{datetime.datetime.now().timestamp()}"

            with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix) as tempdir:
                files_loaded = 0
                for dirname in download_paths:
                    # chdir to be on top dir level
                    sftp.chdir(None)
                    # sftp.chdir(download_directory)

                    if dirname:
                        print("chdir", dirname)
                        sftp.chdir(dirname)
                        local_temp_emar_dir = os.path.join(tempdir, dirname)
                        print("local_temp_emar_dir", local_temp_emar_dir)
                        if not os.path.exists(local_temp_emar_dir):
                            os.mkdir(local_temp_emar_dir)
                            # logger.info(f"Creating equivalent directory on local: {local_temp_emar_dir}")
                            print(f"\nCreating equivalent directory on local: {local_temp_emar_dir}")

                        if isinstance(download_paths[dirname], list):
                            # TODO handle repeated code
                            for filename in download_paths[dirname]:
                                print("checking: {}/{}", dirname, filename)
                                stdin, stdout, stderr = ssh.exec_command(f"sha256sum {filename}")
                                checksum = stdout.read().decode()

                                if dirname not in credentials["files_checksum"]:
                                    sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                                    print("downloaded: {}/{}", dirname, filename)
                                    files_loaded += 1
                                elif not checksum == credentials["files_checksum"][dirname][filename]:
                                    sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                                    print("downloaded: {}/{}", dirname, filename)
                                    files_loaded += 1
                                else:
                                    print("NOT downloaded: {}/{} file is not changed", dirname, filename)
                    else:
                        # TODO handle repeated code
                        for filename in download_paths[dirname]:
                            print("checking: {}/{}", dirname, filename)
                            stdin, stdout, stderr = ssh.exec_command(f"sha256sum {filename}")
                            checksum = stdout.read().decode()

                            if dirname not in credentials["files_checksum"]:
                                sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                                print("downloaded: {}/{}", dirname, filename)
                                files_loaded += 1
                            elif not checksum == credentials["files_checksum"][dirname][filename]:
                                print("checking: {}/{}", dirname, filename)
                                sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                                files_loaded += 1
                            else:
                                print("NOT downloaded: {}/{} file is not changed", dirname, download_paths[dirname])

                sftp.close()
                
                if files_loaded > 0:
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
                    from pprint import pprint

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    dirs = [i for i in files if "\\" not in i]
                    pprint(dirs)
                    dirs.sort(key = lambda x: x.split("timestamp")[1])

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

                    pprint(f"dirs:\n{dirs}")

                    proc = Popen([Path(".") / "7z.exe", "l", "-ba", "-slt", zip_name], stdout=PIPE)
                    files = [l.split('Path = ')[1] for l in proc.stdout.read().decode().splitlines() if l.startswith('Path = ')]
                    dirs = [i for i in files if "\\" not in i]
                    pprint(f"after d dirs:\n{dirs}")
                    
                else:
                    logger.info("Nothing to zip.")

                update_download_status("downloaded", credentials, last_downloaded=str(tempdir))


@logger.catch
def send_activity(last_download_time, creds):
    if os.path.isfile(local_creds_json):
        with open(local_creds_json, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {local_creds_json}.")
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
    else:
        manager_host = g_manager_host

    url = f"{manager_host}/last_time"
    requests.post(url, json={
    "company_name": creds["company_name"],
    "identifier_key": creds["identifier_key"],
    "location_name": creds["location_name"],
    "last_download_time": str(last_download_time),
    "last_time_online": str(datetime.datetime.now())
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

    url = f"{manager_host}/download_status"
    requests.post(url, json={
    "company_name": creds["company_name"],
    "location_name": creds["location_name"],
    "download_status": status,
    "last_time_online": str(datetime.datetime.now()),
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
        # last_download_time = datetime.datetime.now()  # TODO for testing purpose, remove in prod
        send_activity(last_download_time, credentials)
        logger.info("Downloading proccess finished.")

        import getpass
        user = getpass.getuser()

        path = fr"C:\\Users\\{user}\\Desktop\\EMAR.lnk"  #This is where the shortcut will be created

        if not os.path.exists(path):

            from win32com.client import Dispatch

            progs = "Program Files (x86)" if os.path.exists("C:\\Program Files (x86)") else "Program Files"
            target = fr"C:\\{progs}\\CheckRemoteUpdate\\zip_backups\\emar_backups.zip" # directory to which the shortcut is created
            wDir = fr"C:\\{progs}\\CheckRemoteUpdate\\zip_backups"

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
    time.sleep(60)
except Exception as e:
    print(f"Exception occured: {e}")
    time.sleep(120)

