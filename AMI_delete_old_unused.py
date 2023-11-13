import argparse
import datetime

import boto3
from dateutil import parser

# deregister old and not frequently used amis. input a csv of the amis you want to check.
# This will delete any that are older than 600 days and have not been used in the last 300 days
# usage: python3 AMI_delete_old_unused.py ami.csv


def get_days_old(ami_creation_date):
    creation_date = parser.parse(ami_creation_date)
    return (datetime.datetime.now(creation_date.tzinfo) - creation_date).days


def get_last_launch_time(ami_id, client):
    try:
        response = client.describe_image_attribute(
            Attribute="lastLaunchedTime", ImageId=ami_id
        )
        last_launched_time = response.get("LastLaunchedTime", {}).get("Value")
        if last_launched_time:
            return parser.parse(last_launched_time)
    except Exception as e:
        print(f"Error retrieving last launch time for {ami_id}: {e}")


def main(file_name):
    # Read the list of AMI IDs from the file
    with open(file_name) as f:
        ami_ids = f.read().split(",")

    ec2 = boto3.resource("ec2")
    client = boto3.client("ec2")

    for ami_id in ami_ids:
        ami_id = ami_id.strip()
        try:
            ami = ec2.Image(ami_id)
            days_old = get_days_old(ami.creation_date)

            if days_old > 600:
                last_launch_time = get_last_launch_time(ami_id, client)
                if last_launch_time:
                    days_since_last_launch = (
                        datetime.datetime.now(last_launch_time.tzinfo)
                        - last_launch_time
                    ).days
                    if days_since_last_launch > 300:
                        print(
                            f"Deleting {ami_id}, last used {days_since_last_launch} days ago."
                        )
                        client.deregister_image(ImageId=ami_id)
                else:
                    print(f"Deleting {ami_id}, never launched.")
                    client.deregister_image(ImageId=ami_id)

        except Exception as e:
            print(
                f"Error processing {ami_id}: {e}. You might have already deleted the image."
            )


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Delete AMIs older than 600 days and not used in the last 6 months."
    )
    arg_parser.add_argument(
        "file_name", type=str, help="File containing a comma-separated list of AMI IDs"
    )
    args = arg_parser.parse_args()

    main(args.file_name)
