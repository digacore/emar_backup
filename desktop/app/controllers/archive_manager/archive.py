from subprocess import Popen, PIPE
import re

from app.consts import SEVEN_ZIP

from .exception import ArchiveException
from .archive_item import ArchiveItem, ItemType

__TEMPLATE_STR = (
    r"^Path\s=\s(?P<name>.+)\r\n"
    r"Folder\s=\s(?P<folder>.+)\r\n"
    r"Size\s=\s(?P<size>\d+)\r\n"
    r"Packed\sSize\s=\s(?P<packed_size>\d+)\r\n"
    r"Modified\s=\s(?P<modified>.+)\r\n"
    r"Created\s=\s(?P<created>.+)\r\n"
    r"Accessed\s=\s(?P<accessed>.+)\r\n"
    r"Attributes\s=\s(?P<attributes>.+)\r\n"
    r"Encrypted\s=\s(?P<encrypted>.*)\r\n"
    r"Comment\s=\s(?P<comment>.*)\r\n"
    r"CRC\s=\s(?P<crc>.*)\r\n"
    r"Method\s=\s(?P<method>.*)\r\n"
    r"Host\sOS\s=\s(?P<host_os>.+)\r\n"
    r"Version\s=\s(?P<version>.+)\r\n"
)

# __TEMPLATE_STR = r"^Path\s=\s(?P<name>.+)\r\nFolder"


RE_ZIP_ITEM_INFO = re.compile(__TEMPLATE_STR, re.MULTILINE | re.VERBOSE)


class Archive:
    def __init__(self, path: str, password: str = None):
        self.path = path
        self.password = password
        self.seven_zip = str(SEVEN_ZIP)

    def add_item(self, local_path: str):
        args = [self.seven_zip, "a"]
        if self.password:
            args += [f"-p{self.password}"]
        args += [self.path, local_path]
        process = Popen(
            args,
            stdout=PIPE,
            stderr=PIPE,
        )

        stdout_res, stderr_res = process.communicate()
        if "Everything is Ok" not in stdout_res.decode():
            if stderr_res:
                raise ArchiveException(stderr_res.decode())
            raise ArchiveException(stdout_res.decode())

    def dir(self, archive_path: str = "") -> list[ArchiveItem]:
        args = [self.seven_zip, "l", "-slt", self.path]
        if self.password:
            args += [f"-p{self.password}"]
        proc = Popen(
            args,
            stdout=PIPE,
            stderr=PIPE,
        )

        stdout_res, stderr_res = proc.communicate()

        if stderr_res:
            raise ArchiveException(stderr_res.decode())

        output = stdout_res.decode()
        assert output

        items = []
        for match in RE_ZIP_ITEM_INFO.finditer(output):
            item = ArchiveItem(
                name=match.group("name"),
                item_type=ItemType.FOLDER if match.group("folder") == "+" else ItemType.FILE,
                size=int(match.group("size")),
                packed_size=int(match.group("packed_size")),
                modified=match.group("modified"),
                created=match.group("created"),
                accessed=match.group("accessed"),
                attributes=match.group("attributes"),
                encrypted=match.group("encrypted"),
                comment=match.group("comment"),
                crc=match.group("crc"),
                method=match.group("method"),
                host_os=match.group("host_os"),
                version=match.group("version"),
            )

            if archive_path:
                if "\\" in item.name:
                    if item.name.startswith(archive_path) and "\\" not in item.name[len(archive_path) + 1 :]:
                        items.append(item)
            else:
                if "\\" not in item.name:
                    items.append(item)

        return items

    def delete(self, item: str):
        args = [self.seven_zip, "d", "-r", self.path, item]
        if self.password:
            args += [f"-p{self.password}"]
        process = Popen(
            args,
            stdout=PIPE,
            stderr=PIPE,
        )

        stdout_res, stderr_res = process.communicate()
        if "Everything is Ok" not in stdout_res.decode():
            if stderr_res:
                raise ArchiveException(stderr_res.decode())
            raise ArchiveException(stdout_res.decode())
