

def test_get_computers(client):

    response = client.get("/get_computers")

    assert response
    assert response.json["comp1_intime"]
    assert "comp1_intime" in response.json


def test_register_computer(client):

    response = client.post(
        "/register_computer",
        json=dict(
            identifier_key="new_computer",
            computer_name="new_test_computer"
        )
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "registered"
    assert "new_test_computer" in response.json["computer_name"]

    response = client.post(
        "/register_computer",
        json=dict(
            identifier_key="new_computer",
            computer_name="new_test_computer"
        )
    )

    assert response
    assert response.status_code == 409
    assert response.json["status"] == "fail"

    response = client.post(
        "/register_computer",
        json=dict(
            identifier_key="fbsfvdsbsbgrbfb",
            computer_name="new_test_computer"
        )
    )

    assert response
    assert response.status_code == 409
    assert response.json["status"] == "fail"

    response = client.post(
        "/register_computer",
        json=dict(
            identifier_key=111,
            computer_name=222
        )
    )

    assert response
    assert response.status_code == 400
    assert response.json["status"] == "fail"
