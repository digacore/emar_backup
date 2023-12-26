import argparse

from app.logger import logger
from app import controllers as c


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-sc", "--server-connect", action="store_true")
    group.add_argument("-hb", "--heartbeat", action="store_true")
    group.add_argument("-del", "--computer-delete", action="store_true")
    group.add_argument("-l", "--log-convertor", action="store_true")

    args = parser.parse_args()

    if args.heartbeat:
        logger.info("Heartbeat")
        c.heartbeat()
    elif args.server_connect:
        logger.info("Server connect")
        c.server_connect()
    elif args.computer_delete:
        logger.info("Computer delete")
        c.computer_delete()
    elif args.log_convertor:
        print("Log convertor started.")
        c.log_convertor()
        print("Log convertor finished.")
    else:
        logger.error("No arguments passed")


if __name__ == "__main__":
    main()
