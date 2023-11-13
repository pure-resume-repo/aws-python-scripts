import argparse

import boto3

"""
1. To get snapshots created before a specific date:
python script_name.py --before 2022-01-01

2. To get snapshots created after a specific date:
python script_name.py --after 2022-01-01
"""


def get_all_snapshots(before_date, after_date):
    ec2_client = boto3.client("ec2")
    paginator = ec2_client.get_paginator("describe_snapshots")
    snapshot_ids = []

    # Define filters based on provided dates
    filters = []
    if before_date:
        filters.append({"Name": "start-time", "Values": [f"{before_date}T00:00:00Z"]})

    if after_date:
        filters.append({"Name": "start-time", "Values": [f"{after_date}T00:00:00Z"]})

    for page in paginator.paginate(Filters=filters):
        for snapshot in page["Snapshots"]:
            snapshot_ids.append(snapshot["SnapshotId"])

    return snapshot_ids


def main():
    parser = argparse.ArgumentParser(
        description="Filter AWS EBS snapshots based on dates."
    )
    parser.add_argument(
        "--before",
        type=str,
        help="Fetch snapshots created before this date in the format YYYY-MM-DD.",
    )
    parser.add_argument(
        "--after",
        type=str,
        help="Fetch snapshots created after this date in the format YYYY-MM-DD.",
    )

    args = parser.parse_args()

    if not args.before and not args.after:
        print("Please provide either --before or --after date.")
        return

    snapshot_ids = get_all_snapshots(args.before, args.after)

    for snapshot_id in snapshot_ids:
        print(snapshot_id)


if __name__ == "__main__":
    main()
