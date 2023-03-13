def test_search_column(client):

    response = client.post(
        "/search_column",
        json=dict(
            col_name="computer_name",
        ),
    )

    assert response
    assert response.json["status"] == "success"

    response = client.post(
        "/search_column",
        json=dict(
            col_name="name_computer",
        ),
    )

    assert response
    assert response.json["status"] == "fail"
