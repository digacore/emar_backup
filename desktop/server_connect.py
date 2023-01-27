import os
import sys
import subprocess
import stat
import time
import datetime
import json
import hashlib
import requests
from pathlib import Path
import socket
import tempfile

# from zipfile import ZipFile
# file_name = "XYZ.zip"
# with ZipFile(file_name, "r") as zip:
#     zip.extractall(path="uncompressed", pwd="password".encode("utf-8"))
from paramiko import SSHClient, AutoAddPolicy, AutoAddPolicy
from loguru import logger


log_format = "{time} - {name} - {level} - {message}"
# logger.add(sys.stdout, format=log_format, serialize=True, level="DEBUG", colorize=True)
# TODO for prod write to desktop
logger.add(sink=Path().home().joinpath("Desktop/emar_backup.txt"), format=log_format, serialize=True, level="DEBUG", colorize=True)


def mknewdir(pathstr):
    if not os.path.exists(pathstr):
        os.mkdir(pathstr)


backups_path = Path("C:") / "backups"
g_manager_host = "http://localhost:5000"


if os.path.isfile(Path("config.json").absolute()):
    with open("config.json", "r") as f:
        config_json = json.load(f)
    try:
        backups_path = config_json["backups_path"]
        g_manager_host = config_json["manager_host"]
    except Exception as e:
        logger.warning(f"Failed to get info from config.json. Proceeding with default. Error: {e}")


mknewdir(backups_path)

timestr = f"backup_{time.ctime()}".replace(":", "_").replace(" ", "_")
# local_path = f"{backups_path}\\{timestr}"
local_path = Path(backups_path) / timestr

mknewdir(local_path)

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

    else:
        computer_name = socket.gethostname()
        identifier_key = "new_computer"

        response = requests.post(f"{g_manager_host}/register_computer", json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        })
        logger.info(f"New computer registered. Download will start next time if credentials inserted to DB.")
    print(response.json())
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
            for file_lvl_1 in sftp.listdir_attr():

                # TODO is it reasonable to update_download_status in loop? May cause a lot of post requests
                # update_download_status("comparing files", credentials)
                # chdir to be on top dir level
                # logger.debug(f"Changing remote directory to start directory.")
                print("Changing remote directory to start directory.")
                sftp.chdir(None)
                print("file_lvl_1", file_lvl_1.filename, file_lvl_1.st_mode, stat.S_ISDIR(file_lvl_1.st_mode))

                if not stat.S_ISDIR(file_lvl_1.st_mode):

                    # local_file_path = f"{local_path}\{file_lvl_1.filename}"
                    # # TODO handle repeated code 
                    # stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                    # checksum = stdout.read()
                    # print("sha256sum lvl1", checksum)
                    # checksum_result = checksum_local_remote(
                    #     f"{local_path}\{file_lvl_1.filename}",
                    #     checksum
                    #     )
                    # TODO is it possible? Can't repeat
                    if None in download_paths:
                        download_paths[file_lvl_1.filename].append(file_lvl_2.filename)
                    else:
                        download_paths[file_lvl_1.filename] = [file_lvl_2.filename]
                    # if checksum_result:
                    #     sftp_download(
                    #         chdir=None,
                    #         filename=file_lvl_1.filename,
                    #         local_file_path=local_file_path,
                    #         creds=credentials)

                elif stat.S_ISDIR(file_lvl_1.st_mode):
                    # logger.info(f"Changing remote directory to {file_lvl_1.filename}")
                    print(f"Changing remote directory to {file_lvl_1.filename}")
                    sftp.chdir(file_lvl_1.filename)

                    # if not os.path.exists(f"{local_path}\{file_lvl_1.filename}"):
                    #     os.mkdir(f"{local_path}\{file_lvl_1.filename}")
                    #     logger.info(f"Creating equivalent directory on local: {file_lvl_1.filename}")

                    for file_lvl_2 in sftp.listdir_attr():

                        # print("file_lvl_2", file_lvl_2, file_lvl_2.st_mode, stat.S_ISDIR(file_lvl_2.st_mode))

                        if not stat.S_ISDIR(file_lvl_2.st_mode):
                            # local_file_path = f"{local_path}\{file_lvl_1.filename}\{file_lvl_2.filename}"

                            # TODO handle repeated code
                            # print(f"lvl2 path: {file_lvl_1.filename}\{file_lvl_2.filename}")
                            # stdin, stdout, stderr = ssh.exec_command(f"sha256sum /{file_lvl_1.filename}/{file_lvl_2.filename}")
                            # checksum = stdout.read()
                            # print("sha256sum lvl2", checksum)
                            # checksum_result = checksum_local_remote(
                            #     f"{local_path}\{file_lvl_1.filename}\{file_lvl_2.filename}",
                            #     checksum
                            #     )
                            if file_lvl_1.filename in download_paths:
                                download_paths[file_lvl_1.filename].append(file_lvl_2.filename)
                            else:
                                download_paths[file_lvl_1.filename] = [file_lvl_2.filename]

                            # if not checksum_result:
                            #     sftp_download(
                            #         chdir=file_lvl_1.filename,
                            #         filename=file_lvl_2.filename,
                            #         local_file_path=local_file_path,
                            #         creds=credentials)

                else:
                    logger.error(f"Something went wrong during check of {file_lvl_1.filename}")
                    continue
        
        sftp_check_download(
            download_paths=download_paths,
            credentials=credentials
        )

    return datetime.datetime.now()


@logger.catch
def sftp_download(chdir, filename, local_file_path, creds):
    with SSHClient() as ssh:
        # TODO check for real key
        ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.connect(
            creds["host"],
            username=creds["sftp_username"],
            password=creds["sftp_password"],
            timeout=10,
            auth_timeout=10
        )
        with ssh.open_sftp() as sftp:
            print("chdir", chdir)
            sftp.chdir(chdir)
            update_download_status("downloading", creds)
            sftp.get(filename, local_file_path)
            sftp.close()


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
            yy = 0
            prefix=f"backup_{time.ctime()}_".replace(":", "_").replace(" ", "_")
            with tempfile.TemporaryDirectory(prefix=prefix) as tempdir:
                for dirname in download_paths:
                    if yy == 1:
                        break
                    sftp.chdir(None)
                    print("chdir", dirname)
                    sftp.chdir(dirname)

                    if dirname:
                        local_temp_emar_dir = os.path.join(tempdir, dirname)
                        print("local_temp_emar_dir", local_temp_emar_dir)
                        if not os.path.exists(local_temp_emar_dir):
                            os.mkdir(local_temp_emar_dir)
                            # logger.info(f"Creating equivalent directory on local: {local_temp_emar_dir}")
                            print(f"\nCreating equivalent directory on local: {local_temp_emar_dir}")

                        if isinstance(download_paths[dirname], list):
                            for filename in download_paths[dirname]:
                                print("downloading", dirname, filename)
                                sftp.get(filename, os.path.join(local_temp_emar_dir, filename))
                                print("downloaded", dirname, filename)
                    else:
                        print("downloading", dirname, download_paths[dirname])
                        sftp.get(download_paths[dirname], local_temp_emar_dir)
                    yy += 1

                sftp.close()
                
                zip_name = Path("C:") / "zip_backups" / "emar_backups.zip"
                print("zip_name", zip_name)
                subprs = subprocess.Popen([
                        Path(".") / "7z.exe",
                        "a",
                        zip_name,
                        tempdir,
                        f'-p{credentials["folder_password"]}'
                    ])
                subprs.communicate()
                logger.info("Files zipped.")
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

