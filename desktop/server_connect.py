import os
import sys
import shutil
import subprocess
import stat
import time
import datetime
import json
import hashlib
import requests
from pathlib import Path
import platform
import socket

from dotenv import load_dotenv
from paramiko import SSHClient, AutoAddPolicy, AutoAddPolicy
from loguru import logger

from zip_encrypt import make_arch_7zip


log_format = "{time} - {name} - {level} - {message}"
logger.add(sys.stdout, format=log_format, serialize=True, level="DEBUG", colorize=True)

load_dotenv()

backups_path = "C:\\backups"
if not os.path.exists(backups_path):
    os.mkdir(backups_path)
local_path = f"{backups_path}\\temp"
manager_host = "http://localhost:5000"


@logger.catch
def get_credentials():
    logger.info("Recieving credentials.")

    creds_file = "creds.json"
    local_file_path = f"{os.getcwd()}\{creds_file}"
    logger.info(f"local_file_path var is {local_file_path}")

    if os.path.isfile(local_file_path):
        with open(creds_file, "r") as f:
            creds_json = json.load(f)
            logger.info(f"Credentials recieved from {creds_file}.")

        print(creds_json, type(creds_json))
        computer_name = creds_json["computer_name"]
        identifier_key = creds_json["identifier_key"]

        response = requests.post(f"{manager_host}/get_credentials", json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        })

    else:
        # computer_name = platform.node()
        computer_name = socket.gethostname()
        identifier_key = "new_computer"
        # computer_name = os.environ['COMPUTERNAME']register_computer

        response = requests.post(f"{manager_host}/register_computer", json={
            "computer_name": computer_name,
            "identifier_key": identifier_key,
        })
        print(type(response.json()), response.json())
        logger.info(f"New computer registered. Download will start next time if credentials inserted to DB.")

    if response.json()["message"] == "Supplying credentials":
        print(type(response.json()), response.json())
        with open(creds_file, "w") as f:
            json.dump(
                {
                    "computer_name": response.json()["computer_name"],
                    "identifier_key": response.json()["identifier_key"]
                },
                f
            )
            logger.info(f"Full credentials recieved from server and {creds_file} updated.")

        return response.json()
    
    else:
        raise ValueError("Wrong response data. Can't proceed without correct credentials.")


@logger.catch
def sftp_check_files_for_update_and_load(credentials):
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
                update_download_status("comparing files", credentials)
                # chdir to be on top dir level
                logger.info(f"Changing remote directory to start directory.")
                sftp.chdir(None)
                print("file_lvl_1", file_lvl_1.filename, file_lvl_1.st_mode, stat.S_ISDIR(file_lvl_1.st_mode))

                if not stat.S_ISDIR(file_lvl_1.st_mode):
                    if not os.path.exists(f"{local_path}"):
                        os.mkdir(f"{local_path}")
                    # load_files(None, file_lvl_1, credentials)
                    local_file_path = f"{local_path}\{file_lvl_1.filename}"
                    # TODO handle repeated code 
                    stdin, stdout, stderr = ssh.exec_command(f"sha256sum {file_lvl_1.filename}")
                    checksum = stdout.read()
                    print("sha256_remote", checksum)
                    checksum_result = checksum_local_remote(
                        f"{local_path}\{file_lvl_1.filename}",
                        checksum
                        )

                    if checksum_result:
                        sftp_download(
                            chdir=None,
                            filename=file_lvl_1.filename,
                            local_file_path=local_file_path,
                            creds=credentials)

                elif stat.S_ISDIR(file_lvl_1.st_mode):
                    logger.info(f"Changing remote directory to {file_lvl_1.filename}")
                    sftp.chdir(file_lvl_1.filename)

                    if not os.path.exists(f"{local_path}\{file_lvl_1.filename}"):
                        if not os.path.exists(f"{local_path}"):
                            os.mkdir(f"{local_path}")
                        os.mkdir(f"{local_path}\{file_lvl_1.filename}")
                        logger.info(f"Creating equivalent directory on local: {file_lvl_1.filename}")

                    for file_lvl_2 in sftp.listdir_attr():
                        yy = 0
                        if yy==1:
                            continue
                        print("file_lvl_2", file_lvl_2, file_lvl_2.st_mode, stat.S_ISDIR(file_lvl_2.st_mode))

                        if not stat.S_ISDIR(file_lvl_2.st_mode):
                            local_file_path = f"{local_path}\{file_lvl_1.filename}\{file_lvl_2.filename}"

                            # TODO handle repeated code
                            print(f"sha256sum {file_lvl_1.filename}\{file_lvl_2.filename}")
                            stdin, stdout, stderr = ssh.exec_command(f"sha256sum /{file_lvl_1.filename}/{file_lvl_2.filename}")
                            checksum = stdout.read()
                            print("sha256_remote", checksum)
                            checksum_result = checksum_local_remote(
                                f"{local_path}\{file_lvl_1.filename}\{file_lvl_2.filename}",
                                checksum
                                )

                            if not checksum_result:
                                sftp_download(
                                    chdir=file_lvl_1.filename,
                                    filename=file_lvl_2.filename,
                                    local_file_path=local_file_path,
                                    creds=credentials)
                                yy+=1

                else:
                    logger.error(f"Something went wrong during check of {file_lvl_1.filename}")
                    continue

        update_download_status("downloaded", credentials)
    
    logger.info("Download complete.")
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


@logger.catch
def checksum_local_remote(local_filepath, checksum_remote):
    sha256_remote = str(checksum_remote).split()[0].lstrip("b'").lower()
    print(str(checksum_remote).split())
    print("sha256_remote: ", sha256_remote)

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
def update_download_status(status, creds):
    url = f"{manager_host}/download_status"
    requests.post(url, json={
    "company_name": creds["company_name"],
    "location_name": creds["location_name"],
    "download_status": status,
    "last_time_online": str(datetime.datetime.now()),
    "identifier_key": creds["identifier_key"],
    })
    logger.info(f"Download status: {status}.")


@logger.catch
def main_func():
    logger.info("Downloading proccess started.")
    credentials = get_credentials() 
    print("\ncredentials", credentials, "\n")
    if credentials["status"] == "success":
        # last_download_time = sftp_check_files_for_update_and_load(credentials)
        # # last_download_time = datetime.datetime.now()  # for testing purpose, remove in prod
        # send_activity(last_download_time, credentials)
        # logger.info("Downloading proccess finished.")

        zip_name = f"/temmm/backup_{time.ctime()}.zip".replace(":", "_").replace(" ", "_")
        print("zip_name", zip_name)
        # make_arch_7zip(local_path, zip_name, credentials["folder_password"])
        subprs = subprocess.Popen([
                'C:\\Program Files (x86)\\7-Zip\\7z.exe',
                'a',
                f'C:{zip_name}',
                f'{local_path}',
                f'-p{credentials["folder_password"]}'
            ])
        subprs.communicate()
        print(f"make_arch_7zip returncode: {subprs.returncode}")
        logger.info("Files zipped.")
    else:
        logger.info(f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}")
        time.sleep(60)

try:
    main_func()
except Exception as e:
    print(f"Exception occured: {e}")
    time.sleep(300)

