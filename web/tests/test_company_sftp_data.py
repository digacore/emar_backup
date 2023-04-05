def test_company_sftp_data(client):

    response = client.post(
        "/sftp_data",
        json=dict(
            company_id=1,
        ),
    )

    assert response
    assert response.status_code == 200
