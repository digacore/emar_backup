from flask import Blueprint, request, jsonify, Response
from flask_login import login_required

from app import models as m, schema as s


search_blueprint = Blueprint("search", __name__, url_prefix="/search")


@search_blueprint.route("/company", methods=["GET"])
@login_required
def search_company() -> Response:
    """Searching company by name

    Returns:
        Response in JSON format
    """
    search_query = request.args.get("q", "", type=str)
    if not search_query:
        search_results = [
            s.SearchCompanyObj.from_orm(company).dict()
            for company in m.Company.query.order_by(m.Company.name).limit(10).all()
        ]
        return jsonify({"results": search_results})

    search_results = (
        m.Company.query.filter(m.Company.name.ilike(f"%{search_query}%"))
        .order_by(m.Company.name)
        .limit(10)
        .all()
    )
    return jsonify(
        {
            "results": [
                s.SearchCompanyObj.from_orm(company).dict()
                for company in search_results
            ]
        }
    )
