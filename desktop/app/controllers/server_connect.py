# import time
import datetime


from app import logger

from app.consts import STORAGE_PATH
from app.utils import get_credentials, sftp_check_files_for_update_and_load
from app.utils.create_desktop_icon import create_desktop_icon
from app.utils.download_file_from_pcc import download_file_from_pcc
from app.utils.self_update import self_update
from app.utils.send_activity import offset_to_est, send_activity
from app.utils.sftp_check_files_for_update_and_load import (
    AppError,
    update_download_status,
)


def server_connect():
    try:
        # NOTE wait randomly from 0 to 1800 sec
        # to spread load on the server
        # NOTE: Check if this is the first script run
        # is_first_run = not os.path.exists(STORAGE_PATH) or (
        #     len(os.listdir(STORAGE_PATH)) == 1
        #     and "emar_log.txt" in os.listdir(STORAGE_PATH)
        # )

        # if not is_first_run:
        #     time.sleep(random.uniform(0, 30 * 60))

        logger.info("Downloading process started.")
        credentials, old_credentials = get_credentials()
        if not credentials:
            raise ValueError("Credentials not supplied. Can't continue.")

        if credentials["status"] == "success":
            # Handle errors in files downloading and zip
            try:
                if not credentials.get("use_pcc_backup"):
                    last_download_time = sftp_check_files_for_update_and_load(
                        credentials
                    )
                else:
                    download_file_from_pcc(credentials)
                    last_download_time = offset_to_est(datetime.datetime.utcnow())
                send_activity(last_download_time, credentials)
                logger.info("Downloading proccess finished.")
            except (AppError, FileNotFoundError):
                update_download_status("error", credentials)
                logger.info("Downloading process interrupted")

            # user = getpass.getuser()

            create_desktop_icon()

            self_update(STORAGE_PATH, credentials, old_credentials)

        elif credentials["status"] == "registered":
            logger.info(
                "New computer registered. Download will start next time if credentials available in DB."
            )

            create_desktop_icon()

        else:
            logger.info(
                f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}"
            )
        # time.sleep(60)
        logger.info("Task finished")
        # time.sleep(20)
    except Exception as e:
        logger.error("Exception occurred: {}", e)
        # time.sleep(120)
