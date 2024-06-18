from app import controllers as c
from app.consts import BASE_DIR


def test_archive_add_item(no_archive):
    path_to_zip = no_archive
    archive = c.Archive(path=path_to_zip)
    archive.add_item(local_path=str(BASE_DIR / "tests/data/test.ico"))
    archive.add_item(local_path=str(BASE_DIR / "tests/data/1"))
    assert len(archive.dir()) == 2
    assert len(archive.dir("1\\")) == 2


def test_re_arc_item():
    from app.controllers.archive_manager.archive import RE_ZIP_ITEM_INFO

    TEST_OUTPUT = "\r\n7-Zip 9.20  Copyright (c) 1999-2010 Igor Pavlov  2010-11-18\r\n\r\nListing archive: c:\\Users\\saint\\simple2b\\emar_backup\\desktop\\tests\\data\\test.zip\r\n\r\n--\r\nPath = c:\\Users\\saint\\simple2b\\emar_backup\\desktop\\tests\\data\\test.zip\r\nType = zip\r\nPhysical Size = 450952\r\n\r\n----------\r\nPath = 1\r\nFolder = +\r\nSize = 0\r\nPacked Size = 0\r\nModified = 2024-04-10 09:24:28\r\nCreated = 2024-04-10 09:23:45\r\nAccessed = 2024-04-10 11:25:14\r\nAttributes = D....\r\nEncrypted = -\r\nComment = \r\nCRC = \r\nMethod = Store\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = 1\\2\r\nFolder = +\r\nSize = 0\r\nPacked Size = 0\r\nModified = 2024-04-10 09:24:24\r\nCreated = 2024-04-10 09:23:45\r\nAccessed = 2024-04-10 11:25:14\r\nAttributes = D....\r\nEncrypted = -\r\nComment = \r\nCRC = \r\nMethod = Store\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = 1\\2\\3\r\nFolder = +\r\nSize = 0\r\nPacked Size = 0\r\nModified = 2024-04-10 09:24:20\r\nCreated = 2024-04-10 09:24:03\r\nAccessed = 2024-04-10 11:25:14\r\nAttributes = D....\r\nEncrypted = -\r\nComment = \r\nCRC = \r\nMethod = Store\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = 1\\2\\3\\eMARVault_256x256.ico\r\nFolder = -\r\nSize = 479411\r\nPacked Size = 112489\r\nModified = 2023-12-01 14:55:36\r\nCreated = 2024-04-10 09:24:20\r\nAccessed = 2024-04-10 12:11:09\r\nAttributes = ....A\r\nEncrypted = -\r\nComment = \r\nCRC = 3C964FB9\r\nMethod = Deflate\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = 1\\2\\eMARVault_256x256.ico\r\nFolder = -\r\nSize = 479411\r\nPacked Size = 112489\r\nModified = 2023-12-01 14:55:36\r\nCreated = 2024-04-10 09:24:24\r\nAccessed = 2024-04-10 12:11:09\r\nAttributes = ....A\r\nEncrypted = -\r\nComment = \r\nCRC = 3C964FB9\r\nMethod = Deflate\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = 1\\eMARVault_256x256.ico\r\nFolder = -\r\nSize = 479411\r\nPacked Size = 112489\r\nModified = 2023-12-01 14:55:36\r\nCreated = 2024-04-10 09:24:28\r\nAccessed = 2024-04-10 11:58:10\r\nAttributes = ....A\r\nEncrypted = -\r\nComment = \r\nCRC = 3C964FB9\r\nMethod = Deflate\r\nHost OS = FAT\r\nVersion = 20\r\n\r\nPath = test.ico\r\nFolder = -\r\nSize = 479411\r\nPacked Size = 112489\r\nModified = 2023-12-01 14:55:36\r\nCreated = 2024-04-10 09:23:20\r\nAccessed = 2024-04-10 11:58:10\r\nAttributes = ....A\r\nEncrypted = -\r\nComment = \r\nCRC = 3C964FB9\r\nMethod = Deflate\r\nHost OS = FAT\r\nVersion = 20\r\n\r\n"
    res = RE_ZIP_ITEM_INFO.findall(TEST_OUTPUT)
    assert len(res) == 7


def test_archive_add_delete(no_archive):
    path_to_zip = no_archive
    archive = c.Archive(path=path_to_zip)
    archive.add_item(local_path=str(BASE_DIR / "tests/data/test.ico"))
    archive.add_item(local_path=str(BASE_DIR / "tests/data/1"))
    assert len(archive.dir()) == 2
    archive.delete("test.ico")
    assert len(archive.dir()) == 1
    archive.delete("1\\2")
    assert len(archive.dir("1\\")) == 1


def test_archive_with_passwd(no_archive):
    path_to_zip = no_archive
    archive = c.Archive(path=path_to_zip, password="123")
    archive.add_item(local_path=str(BASE_DIR / "tests/data/test.ico"))
    archive.add_item(local_path=str(BASE_DIR / "tests/data/1"))
    assert len(archive.dir()) == 2
    archive.delete("test.ico")
    assert len(archive.dir()) == 1
    archive.delete("1\\2")
    assert len(archive.dir("1\\")) == 1
