from subprocess import Popen, PIPE

from app.logger import logger
from app import schemas as s


# Get-Printer | where { $_.PortName -like "*USB*" } | select -Property PrinterStatus,Name | select -first 1 | convertto-json
def get_printer_info_by_posh() -> s.PrinterInfo:
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
        return s.PrinterInfo.model_validate_json(stdout.decode("utf-8"))
    if stderr:
        logger.error("get_printer_info_by_posh: stderr: {}", stderr.decode("utf-8"))
    return s.PrinterInfo()
