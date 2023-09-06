import re
import base64


def get_percentage(all_obj: list, perc_obj: list) -> int:
    """Percentsge for index.html jinja variables calculated in app/views/main.py

    Args:
        all_obj (list): list of all sqla computer object
        perc_obj (list): list of some sqla computer object based on some condition

    Returns:
        int: Percentsge for jinja variables
    """
    percentage = 0 if len(all_obj) == 0 else int((len(perc_obj) / len(all_obj)) * 100)
    return percentage


def get_outdated_status_comps(
    total_computers: list, hours: int, alert_type: str, alert_color: str = None
) -> list:

    """Get outdated computers. At this point when alert status no_download > 4 h or
    offline > 48 h

    Args:
        total_computers (list[Computer]): All computers in database
        hours (int): hours to filter alerts (48 h for offline, 4 h for no backup)
        alert_type (str): offline or backup

    Returns:
        list[Computer]: filtered list of Computer instances
    """
    outdated_comps = (
        [
            comp
            for comp in total_computers
            if int(re.findall(r"\d+", f"{comp.alert_status} 0")[0]) > hours
            and alert_type in comp.alert_status
        ]
        if not alert_color
        else [
            comp
            for comp in total_computers
            if int(re.findall(r"\d+", f"{comp.alert_status} 0")[0]) > hours
            and alert_type in comp.alert_status
            and alert_color in comp.alert_status
        ]
    )
    return outdated_comps


def get_base64_string(string: str) -> str:
    """Convert ordinary string to base64 encoded string

    Args:
        string (str): string to convert

    Returns:
        str: base64 encoded string
    """

    base64_bytes = base64.b64encode(string.encode("ascii"))
    base64_string = base64_bytes.decode("ascii")
    return base64_string


def update_report_data(
    report_data: list[dict], obj_id: int, new_data: dict
) -> list[dict]:
    """Update report data field.
    We need this function in /pcc/scan_activations.html template to change the values in data (JSON field)

    Args:
        report_data (list[dict]): report data
        obj_id (int): id of the object to update
        new_data (dict): new data to update

    Returns:
        list[dict]: updated report data field
    """
    report_data[obj_id].update(new_data)

    return report_data
