import os
from pathlib import Path

from app.consts import STORAGE_PATH


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
