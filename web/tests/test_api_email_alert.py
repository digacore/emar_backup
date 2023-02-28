def test_api_email_alert(client):

    response = client.post(
        "/api_email_alert",
        json=dict(
            from_email="testeem@email.coo",
            to_addresses="emar@support.com",
            subject="test subject",
            body="test body",
            html_body="<h1>h1 test<h1>",
            alerted_target="comp4_test",
            alert_status="red"
        )
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"

    response = client.post(
        "/api_email_alert",
        json=dict(
            identifier_key=111,
            computer_name=222
        )
    )

    assert response
    assert response.status_code == 422
