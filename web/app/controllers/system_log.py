from flask import url_for

from app import models as m
from app.logger import logger


def create_system_log(
    log_type: m.SystemLogType,
    event_object: m.User | m.Computer | m.Company | m.Location | m.Alert,
    created_by: m.User,
):
    """Create new system log.
    To system logs we include: create, update, delete operations with users, computers, companies, locations and alerts

    Args:
        log_type (m.SystemLogType): the type of system log
        event_object (m.User | m.Computer | m.Company | m.Location | m.Alert):
        the object that was created/updated/deleted
        created_by (m.User): user who did this action
    """

    # URL to object edit view
    object_type = log_type.value.split("_")[0].lower()
    object_url = url_for(f"{object_type}.edit_view", id=event_object.id)

    # Object name
    if isinstance(event_object, m.User):
        object_name = event_object.username
    elif isinstance(event_object, m.Computer):
        object_name = event_object.computer_name
    else:
        object_name = event_object.name

    new_log = m.SystemLog(
        log_type=log_type,
        object_id=event_object.id,
        object_name=object_name,
        object_url=object_url,
        created_by_id=created_by.id,
    )

    new_log.save()

    logger.debug("New system log created: {}", new_log)
