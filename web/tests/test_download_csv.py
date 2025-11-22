import csv
import io

from tests.utils import login, register


def test_download_csv(client):
    register("sam")
    response = login(client, "sam")
    assert b"Login successful." in response.data

    response = client.get("/download_csv?search=<<computer_name>>%3Acomp2_late")

    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"

    assert "attachment" in response.headers.get("Content-Disposition", "")
    assert "computers_export.csv" in response.headers.get("Content-Disposition", "")

    csv_content = response.data.decode("utf-8")
    csv_reader = csv.reader(io.StringIO(csv_content))

    rows = list(csv_reader)

    assert len(rows) >= 1

    headers = rows[0]
    expected_headers = [
        "Subscription",
        "Computer Name",
        "Status",
        "Company Name",
        "Location Name",
        "Location Status",
        "Device Type",
        "Last time online",
        "Last download time",
        "Computer IP",
    ]
    assert headers == expected_headers

    if len(rows) > 1:
        first_data_row = rows[1]
        assert len(first_data_row) == len(expected_headers)

        computer_name = first_data_row[1]
        if computer_name:
            assert "comp2_late" in computer_name.lower()


def test_download_csv_without_filters(client):
    register("sam")
    login(client, "sam")

    response = client.get("/download_csv")

    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"

    csv_content = response.data.decode("utf-8")
    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)

    assert len(rows) >= 1
    assert rows[0][1] == "Computer Name"


def test_download_csv_with_date_filter(client):
    register("sam")
    login(client, "sam")

    response = client.get("/download_csv?search=<<last_time_online>>%3A2023-05-26")

    assert response.status_code == 200
    csv_content = response.data.decode("utf-8")

    assert "Computer Name" in csv_content
    assert len(csv_content.split("\n")) >= 1


def test_download_csv_with_flask_admin_filters(client):
    register("sam")
    login(client, "sam")

    # Test Flask-Admin filters: computer_name contains "comp", status contains "line",
    # company_name contains "Atlas", location_name contains "May"
    # This should return computers from Atlas/Maywood
    response = client.get(
        "/download_csv?flt0_0=comp&flt1_7=line&flt2_14=Atlas&flt4_21=May"
    )

    assert response.status_code == 200
    csv_content = response.data.decode("utf-8")

    assert "Computer Name" in csv_content
    assert len(csv_content.split("\n")) >= 1
    # Should return 5 computers from Atlas/Maywood with "comp" in name and status containing "line"
    # (comp1_intime, comp2_late, comp3_test, comp4_test, comp5_test - all have ONLINE or OFFLINE status)
    lines = csv_content.split("\n")
    # Header + 5 computers + empty line at end
    assert len(lines) >= 6, f"Expected at least 6 lines, got {len(lines)}"
