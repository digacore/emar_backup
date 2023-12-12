import argparse

from app import controllers as c


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-svc", "--server-connect", action="store_true")
    group.add_argument("-hbt", "--heartbeat", action="store_true")
    group.add_argument("-cmd", "--computer-delete", action="store_true")
    group.add_argument("-lcn", "--log-convertor", action="store_true")

    args = parser.parse_args()

    if args.heartbeat:
        c.heartbeat()
    elif args.server_connect:
        c.server_connect()
    elif args.computer_delete:
        c.computer_delete()
    elif args.log_convertor:
        c.log_convertor()
    else:
        print("No arguments were passed.")


if __name__ == "__main__":
    main()
