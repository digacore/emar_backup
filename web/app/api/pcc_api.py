import os
from urllib.parse import urljoin
from flask import Response, abort

from app import schema as s, models as m
from app.views.blueprint import BlueprintApi
from app.controllers import get_pcc_2_legged_token, execute_pcc_request
from app.logger import logger
from config import BaseConfig as CFG


pcc_api_blueprint = BlueprintApi("pcc_api", __name__, url_prefix="/pcc_api")


@pcc_api_blueprint.post("/download_backup/<int:pcc_fac_id>")
def download_backup_from_pcc(body: s.GetCredentials, pcc_fac_id: int) -> Response:
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

    # Check that computer has company and location
    if not computer.company or not computer.location:
        logger.error(
            "Can't download backup for computer {}. Company or location is not set",
            computer,
        )
        abort(409, "Company or location is not set")

    # Check that computer's company is not trial and computer is activated
    if computer.company.is_trial or not computer.activated:
        logger.error(
            "Can't download backup for computer {}. Company is trial or computer not activated",
            computer,
        )
        abort(403, "Company is trial")

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
        pcc_fac_id,
        "backup-files",
    )
    url = urljoin(CFG.PCC_BASE_URL, backup_route)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    res = execute_pcc_request(url, headers=headers, stream=True)

    # Create a record about new backup call
    new_backup_call = m.DownloadBackupCall(computer_id=computer.id)
    new_backup_call.save()

    return Response(
        res.iter_content(chunk_size=10 * 1024),
        content_type=res.headers["Content-Type"],
        headers={"Content-Disposition": "attachment; filename=emar_backup.zip"},
    )
