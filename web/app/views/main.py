from flask import render_template, Blueprint
from sqlalchemy import or_
from flask_login import login_required, current_user

from app.models import Company, Location, Computer, User

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
@login_required
def index():
    global_users = {"global", "global-full", "global-view"}

    viewer: User = User.query.filter_by(username=current_user.username).first()

    if str(viewer.asociated_with).lower() in global_users:
        total_companies = len(Company.query.all())
        total_locations = len(Location.query.all())
        total_computers = len(Computer.query.all())
        # TODO find out which computers are required here: NOT stable/latest OR status Red???
        # current_version_date_comp = len(
        #     Computer.query.filter(
        #         or_(Computer.msi_version == "stable", Computer.msi_version == "latest")
        #     ).all()
        # )
        current_version_date_comp = len(
            Computer.query.filter(Computer.alert_status == "red").all()
        )
    else:
        total_companies = len(Company.query.filter_by(name=viewer.asociated_with).all())
        total_locations = (
            len(Location.query.filter_by(company_name=viewer.asociated_with).all())
            if total_companies > 0
            else len(Location.query.filter_by(name=viewer.asociated_with).all())
        )

        total_computers_query = Computer.query.filter(
            or_(
                Computer.company_name == viewer.asociated_with,
                Computer.location_name == viewer.asociated_with,
            )
        )
        total_computers = len(total_computers_query.all())

        # TODO find out which computers are required here: NOT stable/latest OR status Red???
        # current_version_date_comp = len(
        #     total_computers_query.filter(
        #         or_(
        #             Computer.msi_version == "stable",
        #             Computer.msi_version == "latest",
        #         )
        #     ).all()
        # )
        current_version_date_comp = len(
            total_computers_query.filter(
                Computer.alert_status == "red",
            ).all()
        )

    # NOTE use if NOT stable/latest computers are required
    # out_of_date_comp = total_computers - current_version_date_comp
    out_of_date_comp = current_version_date_comp
    out_of_date_comp_pers = (
        0 if total_computers == 0 else int((out_of_date_comp / total_computers) * 100)
    )

    return render_template(
        "index.html",
        total_companies=total_companies,
        total_locations=total_locations,
        total_computers=total_computers,
        out_of_date_comp=out_of_date_comp,
        out_of_date_comp_pers=out_of_date_comp_pers,
    )
