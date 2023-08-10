from datetime import datetime, timedelta
from flask import render_template, Blueprint, request
from flask_login import login_required

from app import models as m, db
from app.controllers import create_pagination, backup_log_on_request_to_view


info_blueprint = Blueprint("info", __name__, url_prefix="/info")


@info_blueprint.route("/computer/<int:computer_id>", methods=["GET"])
@login_required
def computer_info(computer_id):
    computer = m.Computer.query.filter_by(id=computer_id).first_or_404()

    # Update the last computer log information
    if computer.logs_enabled:
        backup_log_on_request_to_view(computer)

    # Paginated logs for table
    computer_logs_query = m.BackupLog.query.filter(
        m.BackupLog.computer_id == computer_id,
        m.BackupLog.start_time >= datetime.utcnow() - timedelta(days=90),
    )

    last_log = computer_logs_query.order_by(m.BackupLog.start_time.desc()).first()

    per_page = request.args.get("per_page", 25, type=int)
    pagination = create_pagination(
        total=m.count(computer_logs_query), page_size=per_page
    )

    # Logs object that will be used for table
    logs = (
        db.session.execute(
            computer_logs_query.order_by(m.BackupLog.start_time.desc())
            .limit(pagination.per_page)
            .offset(pagination.skip)
        )
        .scalars()
        .all()
    )

    # Logs information for chart
    chart_days = request.args.get("chart_days", 7, type=int)

    logs_for_chart = (
        m.BackupLog.query.filter(
            m.BackupLog.computer_id == computer_id,
            m.BackupLog.start_time >= datetime.utcnow() - timedelta(days=chart_days),
        )
        .order_by(m.BackupLog.start_time.asc())
        .all()
    )

    # List objects with different data for chart.
    labels = []
    notes = []
    chart_green_data = []
    chart_yellow_data = []
    chart_red_data = []

    if logs_for_chart:
        log_time = logs_for_chart[0].est_start_time
        log_to_use_index = 0

        current_log_type = None

        # Fill all the list objects with data for every hour
        while log_time < datetime.utcnow():
            labels.append(log_time)
            notes.append(logs_for_chart[log_to_use_index].notes)

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
        last_log=last_log,
        logs=logs,
        page=pagination,
        chart_days=chart_days,
        labels=labels,
        chart_notes=notes,
        chart_green_data=chart_green_data,
        chart_yellow_data=chart_yellow_data,
        chart_red_data=chart_red_data,
    )
