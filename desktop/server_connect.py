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


log_format = "{time} - {name} - {level} - {message}"
# logger.add(sys.stdout, format=log_format, serialize=True, level="DEBUG", colorize=True)
# TODO for prod write to desktop
logger.add(sink=Path(".").absolute(), format=log_format, serialize=True, level="DEBUG", colorize=True)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)


g_manager_host = "http://localhost:5000"

if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Proceeding with default. Error: {e}")

creds_file = "creds.json"
local_creds_json = f"{os.getcwd()}\{creds_file}"
logger.info(f"local_creds_json var is {local_creds_json}")


@logger.catch
def get_credentials():
    logger.info("Recieving credentials.")
    if os.path.isfile(local_creds_json):
        with open(creds_file, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {creds_file}.")

        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]
        manager_host = creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host

        response = requests.post(f"{manager_host}/get_credentials", json={
            "computer_name": computer_name,
            "identifier_key": str(identifier_key),
        })
        print("if response.json()", response.json())

    else:
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
    if response.json()["message"] == "Supplying credentials" or response.json()["message"] == "Computer registered":
        with open(creds_file, "w") as f:
            json.dump(
                {
                    "computer_name": response.json()["computer_name"],
                    "identifier_key": response.json()["identifier_key"],
                    "manager_host": response.json()["manager_host"]
                },
                f
            )
            logger.info(f"Full credentials recieved from server and {creds_file} updated.")

        return response.json()
    
    else:
        raise ValueError("Wrong response data. Can't proceed without correct credentials.")


@logger.catch
def sftp_check_files_for_update_and_load(credentials):

    # key = directory, value = file
    download_paths = {}
    files_cheksum = {}
    print('credentials["files_checksum"]', credentials["files_checksum"], type(credentials["files_checksum"]))

    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.connect(
            credentials["host"],
            username=credentials["sftp_username"],
            password=credentials["sftp_password"],
            timeout=10,
            auth_timeout=10
        )
        update_download_status("connected to remote", credentials)

        with ssh.open_sftp() as sftp:
            # TODO recursive loop, rewrite
            update_download_status("comparing files", credentials)
            for file_lvl_1 in sftp.listdir_attr():
                # chdir to be on top dir level
                # logger.debug(f"Changing remote directory to start directory.")
                print("Changing remote directory to start directory.")
                sftp.chdir(None)
                print("file_lvl_1", file_lvl_1.filename, file_lvl_1.st_mode, stat.S_ISDIR(file_lvl_1.st_mode))

                if not stat.S_ISDIR(file_lvl_1.st_mode):
                    # TODO handle repeated code 
                    if None in download_paths:
                        download_paths[None].append(file_lvl_1.filename)
                        stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                        checksum = stdout.read()
                        files_cheksum[None][file_lvl_1.filename] = checksum
                    else:
                        download_paths[None] = [file_lvl_1.filename]
                        stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                        checksum = stdout.read()
                        files_cheksum[None] = {file_lvl_1.filename: checksum}

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

    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.connect(
            credentials["host"],
            username=credentials["sftp_username"],
            password=credentials["sftp_password"],
            timeout=10,
            auth_timeout=10
        )
        with ssh.open_sftp() as sftp:
            update_download_status("downloading", credentials)
            prefix=f"backup_{time.ctime()}_".replace(":", "-").replace(" ", "_")
            suffix=f"_timestamp{datetime.datetime.now().timestamp()}"

            with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix) as tempdir:
                files_loaded = 0
                for dirname in download_paths:
                    sftp.chdir(None)

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
                        if None not in credentials["files_checksum"]:
                            sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                            print("downloaded: {}/{}", dirname, filename)
                            files_loaded += 1
                        elif not checksum == credentials["files_checksum"][None][download_paths[dirname]]:
                            print("checking: {}/{}", dirname, download_paths[dirname])
                            sftp.get(download_paths[dirname], local_temp_emar_dir)
                            files_loaded += 1
                        else:
                            print("NOT downloaded: {}/{} file is not changed", dirname, download_paths[dirname])

                sftp.close()
                
                if files_loaded > 0:
                    zip_name = Path("C:/") / "zip_backups" / "emar_backups.zip"
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
def checksum_local_remote(local_filepath, checksum_remote):
    sha256_remote = str(checksum_remote).split()[0].lstrip("b'").lower()
    print("local_filepath", local_filepath)

    if os.path.exists(local_filepath):
        with open(local_filepath, 'rb') as file_to_check:
            data = file_to_check.read()
            sha256_local = hashlib.sha256(data).hexdigest()
            # sha256_local = hashlib.sha256(data).hexdigest()
        print("sha256_local", sha256_local)

        if sha256_remote == sha256_local:
            print("sha256 verified.")
            return True
    else:
        print("sha256 verification failed!.")
        return False


@logger.catch
def send_activity(last_download_time, creds):
    if os.path.isfile(local_creds_json):
        with open(creds_file, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {creds_file}.")
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
        with open(creds_file, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {creds_file}.")
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

