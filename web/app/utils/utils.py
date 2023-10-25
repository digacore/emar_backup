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
    We need this function in /pcc/creation-reports.html template to change the values in data (JSON field)

    Args:
        report_data (list[dict]): report data
        obj_id (int): id of the object to update
        new_data (dict): new data to update

    Returns:
        list[dict]: updated report data field
    """
    report_data[obj_id].update(new_data)

    return report_data
