from flask import render_template, Blueprint
from sqlalchemy import or_

from app.models import Company, Location, Computer

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
def index():

    total_companies = len(Company.query.all())
    total_locations = len(Location.query.all())
    total_computers = len(Computer.query.all())
    current_version_date_comp = len(Computer.query.filter(
            or_(Computer.msi_version == "stable", Computer.msi_version == "stable")
        ).all()
    )
    out_of_date_comp = total_computers - current_version_date_comp
    out_of_date_comp_pers = int((out_of_date_comp / total_computers)*100)

    return render_template(
        "index.html",
        total_companies=total_companies,
        total_locations=total_locations,
        total_computers=total_computers,
        out_of_date_comp=out_of_date_comp,
        out_of_date_comp_pers=out_of_date_comp_pers
    )
