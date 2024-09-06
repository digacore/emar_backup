def test_delete_computer(client):
    response = client.post(
        "/",
        json=dict(identifier_key="new_computer", computer_name="new_test_computer"),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "registered"
    assert "new_test_computer" in response.json["computer_name"]

    id = response.json["identifier_key"]
    assert id
    url = f"/delete_computer?identifier_key={id}"
    response = client.get(
        url,
    )

    assert response


def test_register_computer_lid(client):
    response = client.post(
        "/register_computer_lid",
        json=dict(
            identifier_key="new_computer", computer_name="new_test_computer", lid=1
        ),
    )

    assert response
    assert response.status_code == 200
    assert response.json["status"] == "success"
    assert "new_test_computer" in response.json["computer_name"]
