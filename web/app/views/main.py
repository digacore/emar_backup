from flask import render_template, Blueprint
from sqlalchemy import or_
from sqlalchemy.orm import Query
from flask_login import login_required, current_user

from app.models import (
    Location,
    LocationStatus,
    Computer,
    ComputerStatus,
    DeviceRole,
    User,
    UserPermissionLevel,
)
from app.utils import get_percentage

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
@login_required
def index():
    viewer: User = User.query.filter_by(id=current_user.id).first()

    match viewer.permission:
        case UserPermissionLevel.GLOBAL:
            total_locations_query: Query = Location.query
            total_computers_query: Query = Computer.query
        case UserPermissionLevel.COMPANY:
            total_locations_query: Query = Location.query.filter_by(
                company_id=viewer.company_id
            )
            total_computers_query = Computer.query.filter(
                or_(
                    Computer.company_id == viewer.company_id,
                    Computer.location_id.in_(
                        [loc.id for loc in total_locations_query.all()]
                    ),
                )
            )
        case UserPermissionLevel.LOCATION_GROUP:
            location_ids = [loc.id for loc in viewer.location_group[0].locations]
            total_locations_query: Query = Location.query.filter(
                Location.id.in_(location_ids)
            )
            total_computers_query: Query = Computer.query.filter(
                Computer.location_id.in_(location_ids),
            )
        case UserPermissionLevel.LOCATION:
            total_locations_query: Query = Location.query.filter(
                Location.id == viewer.location[0].id
            )
            total_computers_query = Computer.query.filter(
                Computer.location_id == viewer.location[0].id
            )

    # Count locations information
    locations_offline_query: Query = total_locations_query.filter(
        Location.status == LocationStatus.OFFLINE,
        Location.activated.is_(True),
    )
    locations_offline_perc: float = get_percentage(
        total_locations_query.filter_by(activated=True).all(),
        locations_offline_query.all(),
    )

    locations_online_query: Query = total_locations_query.filter(
        Location.status == LocationStatus.ONLINE,
        Location.activated.is_(True),
    )
    locations_online_perc: float = get_percentage(
        total_locations_query.filter_by(activated=True).all(),
        locations_online_query.all(),
    )

    locations_primary_offline_query: Query = total_locations_query.filter(
        Location.status == LocationStatus.ONLINE_PRIMARY_OFFLINE,
        Location.activated.is_(True),
    )
    locations_primary_offline_perc: float = get_percentage(
        total_locations_query.filter_by(activated=True).all(),
        locations_primary_offline_query.all(),
    )

    # Overall computers information
    computers_online_query: Query = total_computers_query.filter(
        Computer.status == ComputerStatus.ONLINE.value
    )
    computers_online_perc: float = get_percentage(
        total_computers_query.filter_by(activated=True).all(),
        computers_online_query.all(),
    )

    computers_offline_query: Query = total_computers_query.filter(
        Computer.status != ComputerStatus.ONLINE.value,
        Computer.status != ComputerStatus.NOT_ACTIVATED.value.replace("_", " "),
    )
    computers_offline_perc: float = get_percentage(
        total_computers_query.filter_by(activated=True).all(),
        computers_offline_query.all(),
    )

    # Primary computers information
    activated_primary_computers: list[Computer] = total_computers_query.filter(
        Computer.activated.is_(True), Computer.device_role == DeviceRole.PRIMARY
    ).all()
    primary_online_query: Query = total_computers_query.filter(
        Computer.device_role == DeviceRole.PRIMARY,
        Computer.status == ComputerStatus.ONLINE.value,
    )
    primary_online_perc: float = get_percentage(
        activated_primary_computers, primary_online_query.all()
    )

    primary_offline_query: Query = total_computers_query.filter(
        Computer.device_role == DeviceRole.PRIMARY,
        Computer.status != ComputerStatus.ONLINE.value,
        Computer.status != ComputerStatus.NOT_ACTIVATED.value.replace("_", " "),
    )
    primary_offline_perc: float = get_percentage(
        activated_primary_computers, primary_offline_query.all()
    )

    # Alternate computers information
    activated_alternate_computers: list[Computer] = total_computers_query.filter(
        Computer.activated.is_(True), Computer.device_role == DeviceRole.ALTERNATE
    ).all()
    alternate_online_query: Query = total_computers_query.filter(
        Computer.device_role == DeviceRole.ALTERNATE,
        Computer.status == ComputerStatus.ONLINE.value,
    )
    alternate_online_perc: float = get_percentage(
        activated_alternate_computers, alternate_online_query.all()
    )

    alternate_offline_query: Query = total_computers_query.filter(
        Computer.device_role == DeviceRole.ALTERNATE,
        Computer.status != ComputerStatus.ONLINE.value,
        Computer.status != ComputerStatus.NOT_ACTIVATED.value.replace("_", " "),
    )
    alternate_offline_perc: float = get_percentage(
        activated_alternate_computers, alternate_offline_query.all()
    )

    return render_template(
        "index.html",
        total_locations=total_locations_query.count(),
        total_computers=total_computers_query.count(),
        locations_offline=locations_offline_query.count(),
        locations_offline_perc=locations_offline_perc,
        locations_online=locations_online_query.count(),
        locations_online_perc=locations_online_perc,
        locations_primary_offline=locations_primary_offline_query.count(),
        locations_primary_offline_perc=locations_primary_offline_perc,
        computers_online=computers_online_query.count(),
        computers_online_perc=computers_online_perc,
        computers_offline=computers_offline_query.count(),
        computers_offline_perc=computers_offline_perc,
        primary_online=primary_online_query.count(),
        primary_online_perc=primary_online_perc,
        primary_offline=primary_offline_query.count(),
        primary_offline_perc=primary_offline_perc,
        alternate_online=alternate_online_query.count(),
        alternate_online_perc=alternate_online_perc,
        alternate_offline=alternate_offline_query.count(),
        alternate_offline_perc=alternate_offline_perc,
    )
