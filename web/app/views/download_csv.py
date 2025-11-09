import csv
import io
from urllib.parse import unquote

from flask import Blueprint, Response, request
from flask_login import login_required

from app import models as m
from app.logger import logger
from app.views.utils import (
    apply_date_filter,
    apply_join_filter,
    apply_text_filter,
    parse_search_params,
)

download_csv_blueprint = Blueprint("download_csv", __name__, url_prefix="/download_csv")


@download_csv_blueprint.route("", methods=["GET"])
@login_required
def download_csv():
    """Returns csv file with all computers data with filters applied

    Returns:
        csv file: computers data
    """
    logger.info("Generating CSV download for computers")
    search_param = unquote(request.args.get("search", ""))
    filters = parse_search_params(search_param)

    computers_query = m.Computer.query

    # Text filters
    text_mappings = [
        ("computer_name", m.Computer.computer_name),
        ("status", m.Computer.status),
        ("device_role", m.Computer.device_role),
        ("device_type", m.Computer.device_type),
        ("computer_ip", m.Computer.computer_ip),
    ]

    for filter_key, field in text_mappings:
        if filter_key in filters:
            computers_query = apply_text_filter(
                computers_query, field, filters[filter_key]
            )

    # Join filters
    join_mappings = [
        ("company_name", m.Company, m.Company.name),
        ("location_name", m.Location, m.Location.name),
    ]

    for filter_key, join_model, field in join_mappings:
        if filter_key in filters:
            computers_query = apply_join_filter(
                computers_query, join_model, field, filters[filter_key]
            )

    # Date filters
    date_mappings = [
        ("last_time_online", m.Computer.last_time_online),
        ("last_download_time", m.Computer.last_download_time),
    ]

    for filter_key, field in date_mappings:
        if filter_key in filters:
            computers_query = apply_date_filter(
                computers_query, field, filters[filter_key]
            )

    computers = computers_query.all()

    logger.info(f"Found {len(computers)} computers matching filters")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
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
    )

    for computer in computers:
        writer.writerow(
            [
                "Pro" if not computer.is_company_trial else "Lite",
                computer.computer_name or "",
                computer.status or "",
                computer.company_name or "",
                computer.location_name if computer.location else "",
                computer.location_status if computer.location else "",
                computer.device_type or "",
                computer.last_time_online.strftime("%Y-%m-%d %H:%M:%S")
                if computer.last_time_online
                else "",
                computer.last_download_time.strftime("%Y-%m-%d %H:%M:%S")
                if computer.last_download_time
                else "",
                computer.computer_ip or "",
            ]
        )

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    # Return CSV file for download
    logger.info("CSV generation completed, sending file to user")
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=computers_export.csv"},
    )
