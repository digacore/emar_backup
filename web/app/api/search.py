from typing import List

from flask import jsonify

import app

from app.views.blueprint import BlueprintApi
from app.schema import ColumnSearch
from app.utils import MyModelView
from app import models


models_to_search = {
    "company": models.Company,
    "computer": models.Computer,
    "location": models.Location,
    "alert": models.Alert,
}

search_column_blueprint = BlueprintApi("/search_column", __name__)


@search_column_blueprint.post("/search_column")
def search_column(body: ColumnSearch):

    # get list of flask_admin ModelView's from current running app
    model_views: List[MyModelView] = app.admin._views

    for model_view in model_views:
        if not hasattr(model_view, "column_list"):
            continue
        if not model_view.column_list:
            continue

        # get current model name from url
        model_name = body.current_href.split("/")[4]

        # search by model's one column
        if (
            body.col_name in model_view.column_list
            and model_name in str(model_view).lower()
        ):
            old_column_searchable_list = model_view.column_searchable_list
            model_view.column_searchable_list = [body.col_name]
            model_view.init_search()

            return (
                jsonify(
                    status="success",
                    message=f"{model_view.__repr__()} column_searchable_list updated from \
                        {old_column_searchable_list} to {[body.col_name]}",
                ),
                200,
            )

        # search by model's all column
        elif body.col_name == "all" and model_name in str(model_view).lower():
            old_column_searchable_list = model_view.column_searchable_list
            try:
                model_view.column_searchable_list = model_view.column_list
                model_view.init_search()
            except AttributeError:
                model_view.column_searchable_list = model_view.column_filters
                model_view.init_search()

            return (
                jsonify(
                    status="success",
                    message=f"{model_view.__repr__()} column_searchable_list updated from \
                        {old_column_searchable_list} to {[body.col_name]}",
                ),
                200,
            )

    return (
        jsonify(
            status="fail", message=f"Failed to find {body.col_name} in ModelView's"
        ),
        404,
    )
