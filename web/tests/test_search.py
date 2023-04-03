def test_search_column(client):

    response = client.post(
        "/search_column",
        json=dict(
            col_name="computer_name",
            current_href="http://localhost:5000/admin/computer/",
        ),
    )

    assert response
    assert response.json["status"] == "success"

    response = client.post(
        "/search_column",
        json=dict(
            col_name="name_computer",
            current_href="http://localhost:5000/admin/computer/",
        ),
    )

    assert response
    assert response.json["status"] == "fail"
