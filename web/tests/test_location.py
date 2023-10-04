from tests.utils import login, logout

from app import models as m


def test_location_sftp_data(client, test_db):
    test_location = test_db.session.query(m.Location).filter_by(name="Maywood").first()

    # Successful case with global-view user
    login_response = login(client, "test_user_view", "test_user_view")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/{test_location.id}/sftp_data",
    )

    assert response and response.status_code == 200
    assert response.json["default_sftp_path"] == test_location.default_sftp_path

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Successful case with user associated with the location's company
    login_response = login(client, "test_user_company", "test_user_company")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/{test_location.id}/sftp_data",
    )

    assert response and response.status_code == 200
    assert response.json["default_sftp_path"] == test_location.default_sftp_path

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Successful case with user associated with the location
    login_response = login(client, "test_user_location", "test_user_location")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/{test_location.id}/sftp_data",
    )

    assert response and response.status_code == 200
    assert response.json["default_sftp_path"] == test_location.default_sftp_path

    logout_response = logout(client)

    # Unsuccessful case with user not associated with the location, location's company and not global-view
    login_response = login(client, "location_dro_user", "test_user_location")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/{test_location.id}/sftp_data",
    )

    assert response and response.status_code == 403
    assert b"You don&#39;t have access to this location information." in response.data

    logout_response = logout(client)

    # Unsuccessful case with not existing location
    login_response = login(client, "test_user_view", "test_user_view")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/99999/sftp_data",
    )

    assert response and response.status_code == 404


def test_all_locations_list(client, test_db):
    all_locations = m.Location.query.order_by(m.Location.name).all()
    company_locations = (
        test_db.session.query(m.Location)
        .filter_by(company_name="Atlas")
        .order_by(m.Location.name)
        .all()
    )
    one_location = test_db.session.query(m.Location).filter_by(name="Maywood").first()

    # Successful case with global-view user
    login_response = login(client, "test_user_view", "test_user_view")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/",
    )

    assert response and response.status_code == 200
    assert len(response.json["locations"]) == len(all_locations)
    assert response.json["locations"][0] == [all_locations[0].id, all_locations[0].name]

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Successful case with user associated with the company
    login_response = login(client, "test_user_company", "test_user_company")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/",
    )

    assert response and response.status_code == 200
    assert len(response.json["locations"]) == len(company_locations)
    assert response.json["locations"][0] == [
        company_locations[0].id,
        company_locations[0].name,
    ]

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Successful case with user associated with the location
    login_response = login(client, "test_user_location", "test_user_location")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/location/",
    )

    assert response and response.status_code == 200
    assert len(response.json["locations"]) == 1
    assert response.json["locations"][0] == [one_location.id, one_location.name]

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data
