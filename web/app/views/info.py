from datetime import datetime, timedelta
from flask import render_template, Blueprint
from flask_login import login_required

from app import models as m, db
from app.controllers import create_pagination


info_blueprint = Blueprint("info", __name__, url_prefix="/info")


@info_blueprint.route("/computer/<int:computer_id>", methods=["GET"])
@login_required
def computer_info(computer_id):
    computer = m.Computer.query.filter_by(id=computer_id).first_or_404()

    computer_logs_query = m.BackupLog.query.filter(
        m.BackupLog.computer_id == computer_id,
        m.BackupLog.start_time >= datetime.utcnow() - timedelta(days=90),
    )

    pagination = create_pagination(total=m.count(computer_logs_query))

    return render_template(
        "info/computer.html",
        computer=computer,
        logs=db.session.execute(
            computer_logs_query.order_by(m.BackupLog.start_time.desc())
            .limit(pagination.per_page)
            .offset(pagination.skip)
        )
        .scalars()
        .all(),
        page=pagination,
    )
