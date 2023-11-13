import argparse
import sys

import boto3
from dateutil.parser import parse


def list_volumes(state, date, verbose):
    ec2 = boto3.resource("ec2")

    for volume in ec2.volumes.all():
        if volume.create_time.replace(tzinfo=None) < date:
            if state == "all" or state == volume.state:
                if verbose:
                    print(volume.id, volume.state, volume.create_time)
                else:
                    print(volume.id)


def main():
    parser = argparse.ArgumentParser(
        description="List all EBS volumes created before a certain date"
    )
    parser.add_argument(
        "-s",
        "--state",
        choices=["available", "in-use", "all"],
        required=True,
        help="State of the volumes to list: available, in-use, or all",
    )
    parser.add_argument(
        "-d",
        "--date",
        required=True,
        help="Only list volumes created before this date. Format: MM-DD-YYYY",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed information about each volume",
    )

    args = parser.parse_args()

    try:
        date = parse(args.date)
    except ValueError:
        print("Invalid date format. Please use MM-DD-YYYY.")
        sys.exit(1)

    list_volumes(args.state, date, args.verbose)


if __name__ == "__main__":
    main()
