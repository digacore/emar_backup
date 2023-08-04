from flask import render_template, Blueprint
from flask_login import login_required

# from app.models import Computer


info_blueprint = Blueprint("info", __name__, url_prefix="/info")


@info_blueprint.route("/computer/<int:computer_id>", methods=["GET"])
@login_required
def computer_info(computer_id):
    # computer = Computer.query.filter_by(id=computer_id).first_or_404()
    # computer_logs =
    return render_template("info/computer.html")
