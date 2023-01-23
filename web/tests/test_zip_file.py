from pathlib import Path
from zipfile import ZipFile, ZIP_BZIP2

import pyzipper


def test_zip_file():
    with ZipFile(file="test.zip", mode="w", compression=ZIP_BZIP2) as zf:
        eggs_path = Path("tests") / "files" / "eggs.txt"
        zf.write(filename=eggs_path, arcname="eggs.txt")


def test_zip_file_open():
    with ZipFile(file="test.zip", mode="w", compression=ZIP_BZIP2) as zf:
        eggs_path = Path("tests") / "files" / "eggs.txt"
        with open(file=eggs_path, mode="rb") as in_file:
            # with zip.open(name="eggs.txt", mode="w", pwd=b"bubu") as f:
            with zf.open(name="files/eggs.txt", mode="w") as f:
                f.write(in_file.read())


def test_zip_file_pyzipper():
    SECRET = b"bububu"

    with pyzipper.AESZipFile(
        "new_test.zip", "w", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(SECRET)
        # zf.writestr("test.txt", "What ever you do, don't tell anyone!")
        eggs_path = Path("tests") / "files" / "eggs.txt"
        with open(file=eggs_path, mode="rb") as in_file:
            # with zip.open(name="eggs.txt", mode="w", pwd=b"bubu") as f:
            with zf.open(name="files/eggs.txt", mode="w") as f:
                f.write(in_file.read())

    # with pyzipper.AESZipFile("new_test.zip") as zf:
    #     zf.setpassword(secret_password)
    #     my_secrets = zf.read("test.txt")

    with ZipFile(file="test.zip", mode="r") as zf:
        zf.setpassword(SECRET)
        eggs_path = Path("tests") / "files" / "eggs.txt"
        with zf.open(name="files/eggs.txt", mode="r") as f:
            data = f.read()
            assert data
