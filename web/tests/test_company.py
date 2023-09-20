from tests.utils import login, logout

from app import models as m


def test_company_sftp_data(client, test_db):
    test_company = test_db.session.query(m.Company).filter_by(name="Atlas").first()

    # Successful case with global-view user
    login_response = login(client, "test_user_view", "test_user_view")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/company/{test_company.id}/sftp_data",
    )

    assert response and response.status_code == 200
    assert response.json["company_sftp_username"] == test_company.default_sftp_username
    assert response.json["company_sftp_password"] == test_company.default_sftp_password

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Successful case with user associated with the company
    login_response = login(client, "test_user_company", "test_user_company")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/company/{test_company.id}/sftp_data",
    )

    assert response and response.status_code == 200
    assert response.json["company_sftp_username"] == test_company.default_sftp_username
    assert response.json["company_sftp_password"] == test_company.default_sftp_password

    logout_response = logout(client)
    assert b"You were logged out." in logout_response.data

    # Unsuccessful case with user not associated with the company and not global-view
    login_response = login(client, "test_user_location", "test_user_location")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/company/{test_company.id}/sftp_data",
    )

    assert response and response.status_code == 403
    assert b"You don&#39;t have access to this company information." in response.data

    # Unsuccessful case with not existing company
    login_response = login(client, "test_user_view", "test_user_view")
    assert b"Login successful." in login_response.data

    response = client.get(
        f"/company/99999/sftp_data",
    )

    assert response and response.status_code == 404
