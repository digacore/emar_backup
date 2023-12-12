from subprocess import Popen, PIPE
import json

from app import logger


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
