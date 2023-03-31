from flask import jsonify

from app.views.blueprint import BlueprintApi
from app.models import Location, Company

from app.logger import logger


locations_company_blueprint = BlueprintApi(
    "/locations_company", __name__, url_prefix="/locations_company"
)
# TODO split blueprints


@locations_company_blueprint.route("/cid/<int:id>", methods=["GET"])
@logger.catch
def cid(id):
    # TODO protect by login requierd
    if id == 0:
        locations = Location.query.all()
    else:
        company: Company = Company.query.filter_by(id=id).first()
        locations = Location.query.filter_by(company_name=company.name).all()

    res = [(loc.id, loc.name) for loc in locations]

    return jsonify(res), 200
