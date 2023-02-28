def test_download_msi(client):
    response = client.get("/download/1")

    assert response
    assert response.status_code == 302
    # assert response.mimetype == "application/octet-stream" not with @login_required and download_name
    assert isinstance(response.data, bytes)

    # TODO fix this test. It gives 302, before giving 400. It redirects first?
    # response = client.get("/download/543543546")

    # assert response
    # assert response.status_code == 400
    # assert response.json["status"] == "fail"


def test_msi_download_to_local(client):

    response = client.post(
        "/msi_download_to_local",
        json=dict(
            name="test_version",
            version="1.0.1.1",
            flag="stable",
            identifier_key="comp3_identifier_key",
            )
    )

    assert response
    assert response.status_code == 200
    assert response.mimetype == "application/octet-stream"
    assert response.data == b"test_bytes"
