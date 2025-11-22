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

# Date filters
date_mappings = [
    ("last_time_online", m.Computer.last_time_online),
    ("last_download_time", m.Computer.last_download_time),
]

# Join filters
join_mappings = [
    ("company_name", m.Company, m.Company.name),
    ("location_name", m.Location, m.Location.name),
]

# Text filters
text_mappings = [
    ("computer_name", m.Computer.computer_name),
    ("status", m.Computer.status),
    ("device_role", m.Computer.device_role),
    ("device_type", m.Computer.device_type),
    ("computer_ip", m.Computer.computer_ip),
]

download_csv_blueprint = Blueprint("download_csv", __name__, url_prefix="/download_csv")


def apply_flask_admin_filters(query, request_args):
    """Apply Flask-Admin filters from URL parameters

    Flask-Admin filter format: flt{filter_num}_{field_index}=value
    Each field has 7 filter operations (contains, not contains, equals, not equals, empty, not empty, in list)
    Field indices: computer_name(0-6), status(7-13), company_name(14-20), location_name(21-27), etc.

    Args:
        query: SQLAlchemy query object
        request_args: Flask request.args

    Returns:
        Modified query with filters applied
    """
    # Field mapping from ComputerView.searchable_sortable_list
    # Each field has 7 filter slots (0-6 for first field, 7-13 for second, etc.)
    # Note: company_name and location_name are hybrid properties, no JOIN needed
    field_mapping = {
        0: ("computer_name", m.Computer.computer_name),
        7: ("status", m.Computer.status),
        14: ("company_name", m.Computer.company_name),  # Hybrid property
        21: ("location_name", m.Computer.location_name),  # Hybrid property
        28: ("device_type", m.Computer.device_type),
        35: ("device_role", m.Computer.device_role),
        42: ("last_download_time", m.Computer.last_download_time),
        49: ("last_time_online", m.Computer.last_time_online),
        56: ("computer_ip", m.Computer.computer_ip),
    }

    # Parse Flask-Admin filter parameters
    for key, value in request_args.items():
        if not key.startswith("flt"):
            continue

        # Parse filter key: flt{filter_num}_{field_index}
        parts = key.split("_")
        if len(parts) < 2:
            continue

        try:
            field_index = int(parts[1])
        except ValueError:
            continue

        # Find the field this filter applies to
        # Field index uses 7-slot blocks per field
        field_position = (field_index // 7) * 7

        if field_position not in field_mapping:
            logger.warning(
                f"Unknown field index: {field_index} (position {field_position})"
            )
            continue

        field_name, field = field_mapping[field_position]

        # Note: field_index % 7 gives operation type (0=contains, 1=not contains, etc.)
        # For now, we'll treat all operations as "contains"

        # Apply contains filter (works for text, ENUM, and hybrid property fields)
        query = query.filter(field.ilike(f"%{value}%"))
        logger.info(f"Applied filter: {field_name} contains '{value}'")

    return query


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

    # Use ComputerView to get the base query with permission filtering
    from app.models import ComputerView
    from app import db
    from flask_login import current_user

    computer_view = ComputerView(m.Computer, db.session)
    computers_query = computer_view.get_query()

    # Log initial count after permission filtering
    initial_count = computers_query.count()
    logger.info(
        f"After permission filtering: {initial_count} computers (user: {current_user.username}, permission: {current_user.permission})"
    )

    # Apply Flask-Admin filters if present
    computers_query = apply_flask_admin_filters(computers_query, request.args)

    # Log count after Flask-Admin filters
    after_admin_filters_count = computers_query.count()
    logger.info(f"After Flask-Admin filters: {after_admin_filters_count} computers")

    for filter_key, field in text_mappings:
        if filter_key in filters:
            computers_query = apply_text_filter(
                computers_query, field, filters[filter_key]
            )

    for filter_key, join_model, field in join_mappings:
        if filter_key in filters:
            computers_query = apply_join_filter(
                computers_query, join_model, field, filters[filter_key]
            )

    for filter_key, field in date_mappings:
        if filter_key in filters:
            computers_query = apply_date_filter(
                computers_query, field, filters[filter_key]
            )

    computers = computers_query.all()

    logger.info(f"Found {len(computers)} computers matching filters")

    with io.StringIO() as output:
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

    # Return CSV file for download
    logger.info("CSV generation completed, sending file to user")
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=computers_export.csv"},
    )
