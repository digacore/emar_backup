from app.logger import logger
from app.utils import (
    get_credentials,
    self_update,
)
from app.utils.version import Version


@logger.catch
def upgrade_program():
    logger.info("Check program version process started.")
    credentials, old_credentials = get_credentials()
    if not credentials:
        raise ValueError("Credentials not supplied. Can't continue.")

    if credentials.status == "success":
        if Version().from_str(credentials.version) > Version().from_str(old_credentials.version):
            logger.info("New version available. Starting self update.")
            self_update(credentials, old_credentials)

    elif credentials.status == "registered":
        logger.info("New computer registered. Update will start next time if credentials available in DB.")

    else:
        logger.info(f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}")
    logger.info("Task finished")
