from subprocess import Popen, PIPE

from app import log


def create_desktop_icon() -> bool:
    """creates desktop icon for eMARVault zip file"""

    # execute: powershell -NonInteractive -WindowStyle Hidden -ExecutionPolicy ByPass -Command .\Create-DesktopShortcut.ps1
    # NOTE: this script is located in the same folder as the zip file
    proc = Popen(
        [
            "powershell.exe",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-ExecutionPolicy",
            "ByPass",
            "-Command",
            ".\\Create-DesktopShortcut.ps1",
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    _, stderr = proc.communicate()
    if proc.returncode == 0:
        log.success("Desktop icon created.")
        return True
    log.error("Desktop icon creation failed: {}", stderr.decode())
    return False
