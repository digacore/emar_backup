from flask import jsonify

from app.views.blueprint import BlueprintApi
from app.models import Company
from app.schema import CompanySFTPData

from app.logger import logger


sftp_data_blueprint = BlueprintApi("/sftp_data", __name__)


@sftp_data_blueprint.post("/sftp_data")
@logger.catch
def sftp_data(body: CompanySFTPData):

    company: Company = Company.query.filter_by(id=body.company_id).first()

    if company:
        message = f"Giving sftp data to company {company.name}."
        logger.info(message)
        return (
            jsonify(
                status="success",
                message=message,
                company_sftp_username=company.default_sftp_username,
                company_sftp_password=company.default_sftp_password,
            ),
            200,
        )

    message = "Wrong request data. Company not found."
    logger.info("MSI download failed. Reason: {}", message)
    return jsonify(status="fail", message=message), 400