import os
from subprocess import Popen, PIPE
import datetime
from pathlib import Path
import time
from urllib.parse import urljoin


import random
import json
import requests
from loguru import logger


# Get-Printer | where { $_.PortName -like "*USB*" } | select -Property PrinterStatus,Name | select -first 1 | convertto-json
def get_printer_info_by_posh() -> dict | None:
    """Get printer info by powershell"""
    logger.info("get_printer_info_by_posh: start")
    PS_COMMAND = "Get-Printer | where { $_.PortName -like '*USB*' } | select -Property PrinterStatus,Name | select -first 1 | ConvertTo-Json"
    shell = Popen(
        [
            "powershell.exe",
            "-command",
            PS_COMMAND,
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout, stderr = shell.communicate()
    logger.info("stdout: {}", stdout)
    if stdout.startswith(b"{"):
        return json.loads(stdout.decode("utf-8"))
    if stderr:
        logger.error("get_printer_info_by_posh: stderr: {}", stderr.decode("utf-8"))


def offset_to_est(dt_now: datetime.datetime):
    """Offset to EST time

    Args:
        dt_now (datetime.datetime): datetime.datetime.utcnow()

    Returns:
        datetime.datetime: EST datetime
    """
    est_norm_datetime = dt_now - datetime.timedelta(hours=5)
    return est_norm_datetime.strftime("%Y-%m-%d %H:%M:%S")


STORAGE_PATH = str(Path("C:\\") / "eMARVault")

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
            "Can't find manager_host in config.json. Check that field and file exist."
        )
else:
    raise FileNotFoundError("Can't find config.json file. Check if file exists.")


CREDS_FILE = "creds.json"
COMPSTAT_FILE = os.path.join(STORAGE_PATH, "compstat.json")
LOCAL_CREDS_JSON = os.path.join(STORAGE_PATH, CREDS_FILE)


@logger.catch
def send_activity(manager_host, creds_json=None):
    if creds_json:
        URL = urljoin(manager_host, "last_time")
        last_time_online = offset_to_est(datetime.datetime.utcnow())
        response = requests.post(
            URL,
            json={
                "computer_name": creds_json["computer_name"],
                "identifier_key": creds_json["identifier_key"],
                "last_time_online": last_time_online,
            },
        )
        logger.info("User last time online {} sent.", last_time_online)

        return response.json()
    else:
        logger.error("Heartbeat app can not find creds.json file.")


@logger.catch
def changes_lookup(comp_remote_data: dict):
    # with open(COMPSTAT_FILE, "r") as f:
    #     compstat = json.load(f)

    # TODO: BUG!!!
    # for field in compstat:
    #     if compstat[field] != comp_remote_data[field]:
    #         subprs = Popen(
    #             [
    #                 Path(".") / "server_connect.exe",
    #             ]
    #         )
    #         subprs.communicate()

    with open(COMPSTAT_FILE, "w") as f:
        json.dump(
            {
                "sftp_host": comp_remote_data["sftp_host"],
                "sftp_username": comp_remote_data["sftp_username"],
                "sftp_folder_path": comp_remote_data["sftp_folder_path"],
                "manager_host": comp_remote_data["manager_host"],
                "msi_version": comp_remote_data["msi_version"],
            },
            f,
        )
        logger.info("Updated computer data was written to compstat.json")


@logger.catch
def send_printer_info(manager_host, creds_json, printer_info):
    URL = urljoin(manager_host, "printer_info")
    response = requests.post(
        URL,
        json={
            "computer_name": creds_json["computer_name"],
            "identifier_key": creds_json["identifier_key"],
            "printer_info": printer_info,
        },
    )
    logger.info("Printer info sent. Response: {}", response.json())

    # check fields: need_send_printer_info

    url = urljoin(creds_json["manager_host"], "get_telemetry_info")
    response = requests.get(
        url,
        json={
            "identifier_key": creds_json["identifier_key"],
        },
    )
    if response.status_code == 404:
        logger.info(
            "Failed to retrieve telemetry info from server. Response: {}",
            response.json(),
        )
    else:
        if response.json()["send_printer_info"]:
            printer_info = get_printer_info_by_posh()
            if printer_info:
                logger.info("Printer info: {}", printer_info)
                # send printer info to server
                send_printer_info(creds_json["manager_host"], creds_json, printer_info)


@logger.catch
def send_printer_info(manager_host, creds_json, printer_info):
    url = urljoin(manager_host, "printer_info")
    response = requests.post(
        url,
        json={
            "computer_name": creds_json["computer_name"],
            "identifier_key": creds_json["identifier_key"],
            "printer_info": printer_info,
        },
    )
    if response.status_code == 404:
        logger.info(
            "Failed to retrieve telemetry info from server. Response: {}",
            response.json(),
        )
    logger.info("Printer info sent. Response: {}", response.json())


@logger.catch
def main_func():
    creds_json = None

    if os.path.isfile(LOCAL_CREDS_JSON):
        with open(LOCAL_CREDS_JSON, "r") as f:
            creds_json = json.load(f)
        manager_host = (
            creds_json["manager_host"] if creds_json["manager_host"] else g_manager_host
        )
    else:
        manager_host = g_manager_host

    if not os.path.isfile(COMPSTAT_FILE):
        with open(COMPSTAT_FILE, "w") as f:
            f.write("{}")

    comp_remote_data = send_activity(manager_host, creds_json)
    changes_lookup(comp_remote_data)


try:
    # NOTE wait randomly from 0 to 279 sec
    # to spread load on the server
    time.sleep(random.uniform(0, 279))
    main_func()
    logger.info("Task finished")
    time.sleep(5)
except Exception as e:
    logger.error("Exception occurred: {}", e)
    time.sleep(20)
