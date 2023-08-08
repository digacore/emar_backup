from datetime import datetime, timedelta
from flask import render_template, Blueprint, request
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

    logs = (
        db.session.execute(
            computer_logs_query.order_by(m.BackupLog.start_time.desc())
            .limit(pagination.per_page)
            .offset(pagination.skip)
        )
        .scalars()
        .all()
    )

    chart_days = request.args.get("chart_days", 7, type=int)

    logs_for_chart = (
        m.BackupLog.query.filter(
            m.BackupLog.computer_id == computer_id,
            m.BackupLog.start_time >= datetime.utcnow() - timedelta(days=chart_days),
        )
        .order_by(m.BackupLog.start_time.asc())
        .all()
    )

    # TODO: check that logs_for_chart is not empty
    log_time = logs_for_chart[0].est_start_time
    log_to_use_index = 0
    labels = []
    notes = []

    chart_green_data = []
    chart_yellow_data = []
    chart_red_data = []

    current_log_type = None
    # prev_log_type = None

    while log_time < datetime.utcnow():
        labels.append(log_time)
        notes.append(logs_for_chart[log_to_use_index].notes)

        # prev_log_type = current_log_type

        if not logs_for_chart[log_to_use_index].error:
            current_log_type = "green"
        elif (
            logs_for_chart[log_to_use_index].error
            == "Longer than 1 hour without a backup"
        ):
            current_log_type = "yellow"
        else:
            current_log_type = "red"

        chart_green_data.append(1 if current_log_type == "green" else None)
        chart_yellow_data.append(1 if current_log_type == "yellow" else None)
        chart_red_data.append(1 if current_log_type == "red" else None)

        log_time += timedelta(hours=1)

        if log_time > logs_for_chart[log_to_use_index].est_end_time:
            log_to_use_index += 1

        if log_to_use_index > len(logs_for_chart) - 1:
            break

    return render_template(
        "info/computer.html",
        computer=computer,
        logs=logs,
        page=pagination,
        chart_days=chart_days,
        labels=labels,
        chart_notes=notes,
        chart_green_data=chart_green_data,
        chart_yellow_data=chart_yellow_data,
        chart_red_data=chart_red_data,
    )
