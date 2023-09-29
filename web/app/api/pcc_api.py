import os
import requests
from urllib.parse import urljoin
from flask import Response, abort

from app import schema as s, models as m
from app.views.blueprint import BlueprintApi
from app.controllers import (
    get_pcc_2_legged_token,
    check_daily_requests_count,
    update_daily_requests_count,
)
from app.logger import logger
from config import BaseConfig as CFG


pcc_api_blueprint = BlueprintApi("pcc_api", __name__, url_prefix="/pcc_api")


@pcc_api_blueprint.post("/download_backup")
def download_backup_from_pcc(body: s.GetCredentials) -> Response:
    # Find computer in DB
    computer: m.Computer = (
        m.Computer.query.filter_by(
            identifier_key=body.identifier_key, computer_name=body.computer_name
        ).first()
        if body.identifier_key and body.computer_name
        else None
    )

    if not computer:
        abort(
            404,
            f"Computer with such credentials not found. Computer_name: \
                {body.computer_name}, identifier_key: {body.identifier_key}",
        )

    # Check that pcc_org_id and pcc_fac_id are present
    if not computer.company.pcc_org_id or not computer.location.pcc_fac_id:
        logger.error(
            "Can't download backup for computer {}. PCC_ORG_ID or PCC_FAC_ID is not set",
            computer,
        )
        abort(409, "PCC_ORG_ID or PCC_FAC_ID is not set")

    # Get 2-legged access token
    token = get_pcc_2_legged_token()

    # Download backup file
    backup_route = os.path.join(
        "api",
        "public",
        "preview1",
        "orgs",
        computer.company.pcc_org_id,
        "facs",
        str(computer.location.pcc_fac_id),
        "backup-files",
    )
    url = urljoin(CFG.PCC_BASE_URL, backup_route)

    # Check daily requests count and raise error if limit is exceeded
    check_daily_requests_count()

    try:
        res = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            cert=(CFG.CERTIFICATE_PATH, CFG.PRIVATEKEY_PATH),
            stream=True,
        )

        # Update daily requests count
        update_daily_requests_count(
            int(res.headers["X-Quota-Time-To-Reset"]),
            int(res.headers["X-Quota-Remaining"]),
        )
    except Exception as e:
        logger.error(
            "Can't download backup from PCC API for computer {}. Reason: {}",
            computer.computer_name,
            e,
        )
        raise e

    return Response(
        res.iter_content(chunk_size=10 * 1024),
        content_type=res.headers["Content-Type"],
        headers={"Content-Disposition": "attachment; filename=emar_backup.zip"},
    )
