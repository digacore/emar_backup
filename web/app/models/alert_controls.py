from datetime import datetime

from sqlalchemy.orm import relationship
from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from celery.schedules import crontab, schedule
from redbeat import RedBeatSchedulerEntry
from worker import app as celery_app

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from app.logger import logger


class AlertControls(db.Model, ModelMixin):
    __tablename__ = "alert_controls"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    alert_interval = db.Column(db.String(64), nullable=False)
    alert_period = db.Column(db.Integer)  # in minutes
    key = db.Column(db.String(128))
    alert = relationship("Alert", passive_deletes=True, lazy="select")
    alert_associated = db.Column(
        db.Integer, db.ForeignKey("alerts.id", ondelete="CASCADE")
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name


class AlertControlsView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "AlertControlsView"

    form_choices = {
        "alert_interval": [
            ("repeat every alert period", "repeat every alert period"),
            ("daily", "daily"),
            ("weekly", "weekly"),
            ("monthly", "monthly"),
        ],
        "name": [
            ("daily_summary", "daily_summary"),
            ("update_cl_stat", "update_cl_stat"),
            ("check_and_alert", "check_and_alert"),
        ],
    }

    action_disallowed_list = ["delete"]

    def on_model_change(self, form, model, is_created):
        alert_hours = int(int(model.alert_period) / 60)
        alert_minutes = int(int(model.alert_period) % 60)

        if model.key:
            try:
                entry = RedBeatSchedulerEntry.from_key(model.key, app=celery_app)
                entry.delete()
            except Exception as e:
                logger.debug("No such record in Redis DB yet. Exception: {}", e)

        if model.alert_interval == "repeat every alert period":
            interval = schedule(run_every=int(model.alert_period) * 60)  # seconds
            entry = RedBeatSchedulerEntry(
                model.name, f"worker.{model.name}", interval, app=celery_app
            )
            entry.save()

            logger.debug(
                "daily_summary interval changed to: {} {}",
                model.alert_period,
                model.alert_interval,
            )

        elif model.alert_interval == "daily":
            interval = crontab(hour=alert_hours, minute=alert_minutes)
            entry = RedBeatSchedulerEntry(
                model.name, f"worker.{model.name}", interval, app=celery_app
            )
            entry.save()
            logger.debug(
                "daily_summary interval changed to: {} {}",
                model.alert_period,
                model.alert_interval,
            )

        elif model.alert_interval == "weekly":
            interval = crontab(hour=alert_hours, minute=alert_minutes, day_of_week=1)
            entry = RedBeatSchedulerEntry(
                model.name, f"worker.{model.name}", interval, app=celery_app
            )
            entry.save()
            logger.debug(
                "daily_summary interval changed to: {} {}",
                model.alert_period,
                model.alert_interval,
            )

        elif model.alert_interval == "monthly":
            interval = crontab(hour=alert_hours, minute=alert_minutes, day_of_month=1)
            entry = RedBeatSchedulerEntry(
                model.name, f"worker.{model.name}", interval, app=celery_app
            )
            entry.save()
            logger.debug(
                "daily_summary interval changed to: {} {}",
                model.alert_period,
                model.alert_interval,
            )

        model.key = entry.key

    def _can_edit(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        # NOTE deletes not allowed as only 2 options are available
        return False

    def allow_row_action(self, action, model):
        if isinstance(action, EditRowAction):
            return self._can_edit(model)

        if isinstance(action, DeleteRowAction):
            return self._can_delete(model)

        # otherwise whatever the inherited method returns
        return super().allow_row_action(action, model)

    # list rows depending on current user permissions
    def get_query(self):
        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
                result_query = self.session.query(self.model)
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False
                result_query = self.session.query(self.model).filter(
                    self.model.name == "None"
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.name == "None"
            )
        return result_query
