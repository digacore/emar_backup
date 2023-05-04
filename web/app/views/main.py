from flask import render_template, Blueprint
from sqlalchemy import or_
from flask_login import login_required, current_user

from app.models import Company, Location, Computer, User, DesktopClient
from app.utils import get_percentage, get_outdated_status_comps

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
@login_required
def index():
    global_users = {"global", "global-full", "global-view"}

    viewer: User = User.query.filter_by(username=current_user.username).first()

    if str(viewer.asociated_with).lower() in global_users:
        total_companies: list[Company] = Company.query.all()
        total_locations: list[Location] = Location.query.all()
        total_computers: list[Computer] = Computer.query.all()

        # TODO find out which computers are required here: NOT stable/latest OR status Red???
        # current_version_date_comp = len(
        #     Computer.query.filter(
        #         or_(Computer.msi_version == "stable", Computer.msi_version == "latest")
        #     ).all()
        # )
        # total_computers_query = Computer.query.filter(Computer.alert_status == "red")

    else:
        total_companies = Company.query.filter_by(name=viewer.asociated_with).all()
        total_locations = (
            Location.query.filter_by(company_name=viewer.asociated_with).all()
            if len(total_companies) > 0
            else Location.query.filter_by(name=viewer.asociated_with).all()
        )

        total_computers = Computer.query.filter(
            or_(
                Computer.company_name == viewer.asociated_with,
                Computer.location_name == viewer.asociated_with,
            )
        ).all()

        # TODO find out which computers are required here: NOT stable/latest OR status Red???
        # current_version_date_comp = len(
        #     total_computers_query.filter(
        #         or_(
        #             Computer.msi_version == "stable",
        #             Computer.msi_version == "latest",
        #         )
        #     ).all()
        # )

    # current_version_date_comp = total_computers_query.filter(
    #     Computer.alert_status == "red",
    # ).all()

    # NOTE use if NOT stable/latest computers are required
    # out_of_date_comp = total_computers - current_version_date_comp
    # out_of_date_comp = len(current_version_date_comp)
    # out_of_date_comp_perc = get_percentage(total_computers, current_version_date_comp)

    # count locations_offline
    locations_status = {loc.name: [] for loc in total_locations}
    # add computers to appropriate location
    for comp in total_computers:
        if comp.location_name:
            locations_status[comp.location_name].append(comp.alert_status)

    # find out in which location all computers are offline
    for loc in locations_status:
        loc_comps_stats = locations_status[loc]  # computers in location
        loc_status_count = 0
        for comp_stat in loc_comps_stats:
            if "offline" in comp_stat:
                loc_status_count += 1
        if loc_status_count == len(loc_comps_stats) and len(loc_comps_stats) != 0:
            locations_status[loc] = "offline"
        else:
            locations_status[loc] = "online"

    locations_offline = [
        loc for loc in locations_status if locations_status[loc] == "offline"
    ]

    locations_offline_perc = get_percentage(total_locations, locations_offline)

    # count locations_no_download
    locations_d_status = {loc.name: [] for loc in total_locations}
    # add computers to appropriate location
    for comp in total_computers:
        if comp.location_name:
            locations_d_status[comp.location_name].append(comp.alert_status)

    # find out in which location allcomputers are no download
    for loc in locations_d_status:
        loc_comps_stats = locations_d_status[loc]  # computers in location
        loc_status_count = 0
        for comp_stat in loc_comps_stats:
            if "no backup" in comp_stat:
                loc_status_count += 1
        if loc_status_count == len(loc_comps_stats) and len(loc_comps_stats) != 0:
            locations_d_status[loc] = "no backup"
        else:
            locations_d_status[loc] = "backup"

    locations_no_download = [
        loc for loc in locations_d_status if locations_d_status[loc] == "no backup"
    ]

    locations_no_download_perc = get_percentage(total_locations, locations_no_download)

    offline_48h = get_outdated_status_comps(total_computers, 48, "offline")
    offline_48h_perc = get_percentage(total_computers, offline_48h)

    no_backup_4h = get_outdated_status_comps(total_computers, 4, "backup")
    no_backup_4h_perc = get_percentage(total_computers, no_backup_4h)

    stable_msi: DesktopClient = DesktopClient.query.filter_by(
        flag_name="stable"
    ).first()

    # create a link for Locations filtering for red cards (danger) at index.html
    offline_1h = get_outdated_status_comps(total_computers, 1, "offline", "red")
    no_backup_1h = get_outdated_status_comps(total_computers, 1, "backup", "red")
    list_filter_str = "?flt2_5="
    alerted_locations_offline = "percen2C".join(
        list(
            set(
                [
                    comp.location_name.replace(" ", "+").replace("&", "%26")
                    for comp in offline_1h
                    if comp.location_name
                ]
            )
        )
    )
    alerted_locations_no_backup = "percen2C".join(
        list(
            set(
                [
                    comp.location_name.replace(" ", "+").replace("&", "%26")
                    for comp in no_backup_1h
                    if comp.location_name
                ]
            )
        )
    )

    al_loc_off_filter_link = f"{list_filter_str}{alerted_locations_offline}"
    al_loc_no_back_filter_link = f"{list_filter_str}{alerted_locations_no_backup}"

    return render_template(
        "index.html",
        total_companies=len(total_companies),
        total_locations=len(total_locations),
        total_computers=len(total_computers),
        # out_of_date_comp=out_of_date_comp,
        # out_of_date_comp_perc=out_of_date_comp_perc,
        locations_offline=len(locations_offline),
        locations_offline_perc=locations_offline_perc,
        locations_no_download=len(locations_no_download),
        locations_no_download_perc=locations_no_download_perc,
        offline_48h=len(offline_48h),
        offline_48h_perc=offline_48h_perc,
        no_backup_4h=len(no_backup_4h),
        no_backup_4h_perc=no_backup_4h_perc,
        stable_msi=stable_msi.version,
        al_loc_off_filter_link=al_loc_off_filter_link,
        al_loc_no_back_filter_link=al_loc_no_back_filter_link,
    )
