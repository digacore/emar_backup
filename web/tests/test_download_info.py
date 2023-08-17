import datetime
from app.models import Computer
from app.api import check_msi_version
from app.schema import LastTime, GetCredentials

from config import BaseConfig as CFG


def test_last_time(client):

    response = client.post(
        "/last_time",
        json=dict(
            identifier_key="comp3_identifier_key",
            computer_name="comp3_test",
            last_time_online=str(datetime.datetime.now()),
        ),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.post(
        "/last_time",
        json=dict(
            identifier_key="comp3_identifier_key",
            computer_name="comp3_test",
            last_time_online=str(datetime.datetime.now()),
            last_download_time=str(datetime.datetime.now()),
        ),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.post(
        "/last_time",
        json=dict(
            identifier_key="WRONG_identifier_key",
            computer_name="comp3_test",
            last_time_online=str(datetime.datetime.now()),
        ),
    )

    assert response
    assert response.status_code == 400
    assert response.json["status"] == "fail"


def test_get_credentials(client):

    response = client.post(
        "/get_credentials",
        json=dict(identifier_key="comp4_identifier_key", computer_name="comp4_test"),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert response.json["identifier_key"] == "comp4_identifier_key"
    assert response.json["computer_name"] == "comp4_test"

    response = client.post(
        "/get_credentials", json=dict(identifier_key=111, computer_name=222)
    )

    assert response
    assert response.status_code == 400
    assert response.json["status"] == "fail"


def test_download_status(client):

    response = client.post(
        "/download_status",
        json=dict(
            company_name="Atlas",
            location_name="Maywood",
            download_status="download_status_test",
            last_time_online=str(datetime.datetime.now()),
            identifier_key="comp3_identifier_key",
            last_downloaded=str(datetime.datetime.now()),
        ),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.post(
        "/download_status",
        json=dict(
            company_name="Atlas",
            location_name="Maywood",
            download_status="download_status_test",
            last_time_online=str(datetime.datetime.now()),
            identifier_key="WRONGgg_identifier_key",
            last_downloaded=str(datetime.datetime.now()),
        ),
    )

    assert response
    assert response.status_code == 400
    assert response.json["status"] == "fail"

    response = client.post(
        "/download_status", json=dict(identifier_key=111, computer_name=222)
    )

    assert response
    assert response.status_code == 422


def test_files_checksum(client):

    # last_time_online: datetime
    # identifier_key: str
    # files_checksum: dict

    response = client.post(
        "/files_checksum",
        json=dict(
            last_time_online=str(datetime.datetime.now()),
            identifier_key="comp3_identifier_key",
            files_checksum=dict(),
        ),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.post(
        "/files_checksum",
        json=dict(
            last_time_online=str(datetime.datetime.now()),
            identifier_key="WRONGgg_identifier_key",
            files_checksum=dict(),
        ),
    )

    assert response
    assert response.status_code == 400
    assert response.json["status"] == "fail"

    response = client.post(
        "/files_checksum", json=dict(identifier_key=111, computer_name=222)
    )

    assert response
    assert response.status_code == 422


def test_check_msi_version(client):

    computer_old_msi: Computer = Computer.query.filter_by(
        computer_name="comp1_intime"
    ).first()
    computer_new_msi: Computer = Computer.query.filter_by(
        computer_name="comp3_test"
    ).first()
    body = LastTime(
        identifier_key="dummy",
        last_download_time=CFG.offset_to_est(datetime.datetime.utcnow(), True),
        last_time_online=CFG.offset_to_est(datetime.datetime.utcnow(), True),
    )

    last_download_old = check_msi_version(computer_old_msi, body, "download")
    last_online_old = check_msi_version(computer_old_msi, body, "online")
    last_download_new = check_msi_version(computer_new_msi, body, "download")
    last_online_new = check_msi_version(computer_new_msi, body, "online")

    assert last_download_old > last_download_new
    assert last_online_old > last_online_new
